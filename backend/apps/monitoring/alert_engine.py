"""
告警引擎
负责评估告警规则和触发告警
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from .models import AlertInstance, AlertRule, MetricData
from .prometheus_client import prometheus_client

logger = logging.getLogger(__name__)


class AlertEngine:
    """告警引擎"""

    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self._rule_cache = {}
        self._last_check_times = {}

    def start(self):
        """启动告警引擎"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()
        logger.info("告警引擎已启动")

    def stop(self):
        """停止告警引擎"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("告警引擎已停止")

    def _check_loop(self):
        """告警检查循环"""
        while self.running:
            try:
                self.check_all_rules()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"告警检查循环错误: {str(e)}")
                time.sleep(self.check_interval)

    def check_all_rules(self):
        """检查所有激活的告警规则"""
        try:
            # 获取所有激活的告警规则
            active_rules = AlertRule.objects.filter(
                status="active", metric_definition__is_enabled=True
            ).select_related("metric_definition")

            for rule in active_rules:
                try:
                    self.check_rule(rule)
                except Exception as e:
                    logger.error(f"检查告警规则失败 {rule.name}: {str(e)}")

            logger.debug(f"完成告警规则检查，共检查 {len(active_rules)} 个规则")

        except Exception as e:
            logger.error(f"获取告警规则失败: {str(e)}")

    def check_rule(self, rule: AlertRule):
        """检查单个告警规则"""
        try:
            # 获取最新的指标值
            latest_value = self._get_latest_metric_value(rule.metric_definition)

            if latest_value is None:
                logger.debug(f"告警规则 {rule.name} 无可用指标数据")
                return

            # 评估规则
            should_trigger = self.evaluate_rule(rule, latest_value)

            if should_trigger:
                self._handle_rule_trigger(rule, latest_value)
            else:
                self._handle_rule_resolve(rule)

        except Exception as e:
            logger.error(f"检查告警规则失败 {rule.name}: {str(e)}")

    def evaluate_rule(self, rule: AlertRule, value: float) -> bool:
        """评估告警规则是否应该触发"""
        threshold = rule.threshold
        operator = rule.operator

        if operator == ">":
            return value > threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<":
            return value < threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.0001  # 浮点数比较
        elif operator == "!=":
            return abs(value - threshold) >= 0.0001
        else:
            logger.warning(f"未知的比较操作符: {operator}")
            return False

    def _get_latest_metric_value(self, metric_definition) -> Optional[float]:
        """获取指标的最新值"""
        try:
            # 首先尝试从Prometheus获取
            prometheus_value = prometheus_client.get_metric_value(
                metric_definition.prometheus_name
            )
            if prometheus_value is not None:
                return prometheus_value

            # 如果Prometheus不可用，从数据库获取
            latest_data = (
                MetricData.objects.filter(metric_definition=metric_definition)
                .order_by("-timestamp")
                .first()
            )

            if latest_data:
                # 检查数据是否过期（超过5分钟）
                if timezone.now() - latest_data.timestamp > timedelta(minutes=5):
                    logger.warning(f"指标 {metric_definition.name} 数据过期")
                    return None

                return latest_data.value

            return None

        except Exception as e:
            logger.error(f"获取指标值失败 {metric_definition.name}: {str(e)}")
            return None

    def _handle_rule_trigger(self, rule: AlertRule, trigger_value: float):
        """处理规则触发"""
        try:
            # 检查是否已经在告警中
            existing_alert = AlertInstance.objects.filter(
                alert_rule=rule, status="firing"
            ).first()

            if existing_alert:
                # 更新现有告警
                existing_alert.trigger_value = trigger_value
                existing_alert.save()
                logger.debug(f"更新现有告警: {rule.name}")
                return

            # 检查持续时间要求
            if not self._check_duration_requirement(rule, trigger_value):
                return

            # 检查是否可以发送告警
            if not rule.can_send_alert():
                logger.debug(f"告警规则 {rule.name} 在静默期内")
                return

            # 创建新的告警实例
            alert_instance = AlertInstance.objects.create(
                alert_rule=rule,
                status="firing",
                message=self._generate_alert_message(rule, trigger_value),
                started_at=timezone.now(),
                trigger_value=trigger_value,
                trigger_labels={},
            )

            # 更新规则状态
            rule.status = "firing"
            rule.total_alerts += 1
            rule.last_alert_at = timezone.now()
            rule.save()

            # 发送通知
            self._send_alert_notification(alert_instance)

            logger.info(f"触发告警: {rule.name} (值: {trigger_value})")

        except Exception as e:
            logger.error(f"处理规则触发失败 {rule.name}: {str(e)}")

    def _handle_rule_resolve(self, rule: AlertRule):
        """处理规则解决"""
        try:
            # 查找正在告警的实例
            firing_alerts = AlertInstance.objects.filter(
                alert_rule=rule, status="firing"
            )

            for alert in firing_alerts:
                alert.resolve()
                logger.info(f"告警已解决: {rule.name}")

            # 更新规则状态
            if rule.status == "firing":
                rule.status = "active"
                rule.save()

        except Exception as e:
            logger.error(f"处理规则解决失败 {rule.name}: {str(e)}")

    def _check_duration_requirement(
        self, rule: AlertRule, trigger_value: float
    ) -> bool:
        """检查持续时间要求"""
        if rule.duration <= 0:
            return True

        # 获取缓存键
        cache_key = f"alert_trigger_{rule.id}"

        # 获取首次触发时间
        first_trigger_time = cache.get(cache_key)
        current_time = timezone.now()

        if first_trigger_time is None:
            # 首次触发，记录时间
            cache.set(cache_key, current_time, rule.duration + 60)
            logger.debug(f"告警规则 {rule.name} 首次触发，开始计时")
            return False

        # 检查是否满足持续时间要求
        duration_elapsed = (current_time - first_trigger_time).total_seconds()

        if duration_elapsed >= rule.duration:
            # 满足持续时间要求，清除缓存
            cache.delete(cache_key)
            return True
        else:
            logger.debug(
                f"告警规则 {rule.name} 持续时间不足: {duration_elapsed}/{rule.duration}秒"
            )
            return False

    def _generate_alert_message(self, rule: AlertRule, trigger_value: float) -> str:
        """生成告警消息"""
        if rule.notification_template:
            # 使用自定义模板
            template = rule.notification_template
            template = template.replace("{rule_name}", rule.name)
            template = template.replace("{metric_name}", rule.metric_definition.name)
            template = template.replace("{trigger_value}", str(trigger_value))
            template = template.replace("{threshold}", str(rule.threshold))
            template = template.replace("{operator}", rule.operator)
            return template
        else:
            # 使用默认模板
            return (
                f"告警规则 '{rule.name}' 已触发\n"
                f"指标: {rule.metric_definition.name}\n"
                f"当前值: {trigger_value}\n"
                f"阈值: {rule.operator} {rule.threshold}\n"
                f"严重程度: {rule.get_severity_display()}\n"
                f"时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

    def _send_alert_notification(self, alert_instance: AlertInstance):
        """发送告警通知"""
        try:
            rule = alert_instance.alert_rule
            channels = rule.notification_channels

            if not channels:
                logger.debug(f"告警规则 {rule.name} 未配置通知渠道")
                return

            notification_data = {
                "rule_name": rule.name,
                "severity": rule.severity,
                "message": alert_instance.message,
                "trigger_value": alert_instance.trigger_value,
                "threshold": rule.threshold,
                "started_at": alert_instance.started_at.isoformat(),
            }

            sent_notifications = []

            for channel in channels:
                try:
                    if channel["type"] == "email":
                        self._send_email_notification(channel, notification_data)
                        sent_notifications.append(channel)
                    elif channel["type"] == "webhook":
                        self._send_webhook_notification(channel, notification_data)
                        sent_notifications.append(channel)
                    elif channel["type"] == "slack":
                        self._send_slack_notification(channel, notification_data)
                        sent_notifications.append(channel)
                    else:
                        logger.warning(f"未知的通知渠道类型: {channel['type']}")

                except Exception as e:
                    logger.error(f"发送通知失败 {channel}: {str(e)}")

            # 更新通知状态
            alert_instance.notifications_sent = sent_notifications
            alert_instance.notification_count = len(sent_notifications)
            alert_instance.save()

            logger.info(
                f"告警通知已发送: {rule.name} ({len(sent_notifications)} 个渠道)"
            )

        except Exception as e:
            logger.error(f"发送告警通知失败: {str(e)}")

    def _send_email_notification(self, channel: Dict, data: Dict):
        """发送邮件通知"""
        from django.conf import settings
        from django.core.mail import send_mail

        subject = f"[{data['severity'].upper()}] {data['rule_name']}"
        message = data["message"]
        recipient_list = channel.get("recipients", [])

        if recipient_list:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False,
            )

    def _send_webhook_notification(self, channel: Dict, data: Dict):
        """发送Webhook通知"""
        import requests

        url = channel.get("url")
        if not url:
            raise ValueError("Webhook URL未配置")

        payload = {"alert": data, "timestamp": timezone.now().isoformat()}

        response = requests.post(
            url, json=payload, timeout=30, headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

    def _send_slack_notification(self, channel: Dict, data: Dict):
        """发送Slack通知"""
        import requests

        webhook_url = channel.get("webhook_url")
        if not webhook_url:
            raise ValueError("Slack Webhook URL未配置")

        # 构建Slack消息
        color = {
            "info": "good",
            "warning": "warning",
            "critical": "danger",
            "fatal": "danger",
        }.get(data["severity"], "warning")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"告警: {data['rule_name']}",
                    "text": data["message"],
                    "fields": [
                        {
                            "title": "严重程度",
                            "value": data["severity"].upper(),
                            "short": True,
                        },
                        {
                            "title": "触发值",
                            "value": str(data["trigger_value"]),
                            "short": True,
                        },
                        {
                            "title": "阈值",
                            "value": str(data["threshold"]),
                            "short": True,
                        },
                        {"title": "时间", "value": data["started_at"], "short": True},
                    ],
                    "timestamp": int(timezone.now().timestamp()),
                }
            ]
        }

        response = requests.post(webhook_url, json=payload, timeout=30)
        response.raise_for_status()

    def test_rule(self, rule: AlertRule, test_value: float) -> Dict:
        """测试告警规则"""
        would_trigger = self.evaluate_rule(rule, test_value)

        return {
            "rule_name": rule.name,
            "test_value": test_value,
            "threshold": rule.threshold,
            "operator": rule.operator,
            "would_trigger": would_trigger,
            "message": (
                self._generate_alert_message(rule, test_value)
                if would_trigger
                else None
            ),
        }

    def force_check_rule(self, rule_id: str):
        """强制检查指定规则"""
        try:
            rule = AlertRule.objects.get(id=rule_id)
            self.check_rule(rule)
            logger.info(f"强制检查告警规则: {rule.name}")
        except AlertRule.DoesNotExist:
            logger.error(f"告警规则不存在: {rule_id}")
        except Exception as e:
            logger.error(f"强制检查告警规则失败: {str(e)}")

    def get_alert_statistics(self) -> Dict:
        """获取告警统计信息"""
        try:
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            stats = {
                "total_rules": AlertRule.objects.count(),
                "active_rules": AlertRule.objects.filter(status="active").count(),
                "firing_rules": AlertRule.objects.filter(status="firing").count(),
                "total_alerts_today": AlertInstance.objects.filter(
                    started_at__gte=today_start
                ).count(),
                "firing_alerts": AlertInstance.objects.filter(status="firing").count(),
                "resolved_alerts_today": AlertInstance.objects.filter(
                    status="resolved", resolved_at__gte=today_start
                ).count(),
                "alerts_by_severity": {},
            }

            # 按严重程度统计
            for severity, _ in AlertRule.SEVERITY_CHOICES:
                count = AlertInstance.objects.filter(
                    alert_rule__severity=severity, status="firing"
                ).count()
                stats["alerts_by_severity"][severity] = count

            return stats

        except Exception as e:
            logger.error(f"获取告警统计失败: {str(e)}")
            return {}


# 全局告警引擎实例
alert_engine = AlertEngine()

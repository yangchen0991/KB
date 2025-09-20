"""
搜索工具函数
"""

import logging
import re
from typing import Any, Dict, List, Optional

from django.db.models import Avg, Count
from django.db.models import Q as DjangoQ
from django.utils import timezone
from elasticsearch_dsl import Q, Search

from .documents import DocumentDocument
from .models import SearchAnalytics, SearchQuery, SearchSuggestion

logger = logging.getLogger(__name__)


class SearchEngine:
    """搜索引擎类"""

    def __init__(self):
        self.document_index = DocumentDocument

    def search_documents(
        self,
        query: str,
        user,
        filters: Dict = None,
        search_type: str = "full_text",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """搜索文档"""
        start_time = timezone.now()

        try:
            # 构建搜索查询
            search = self._build_search_query(query, search_type, filters, user)

            # 分页
            start = (page - 1) * page_size
            search = search[start : start + page_size]

            # 执行搜索
            response = search.execute()

            # 处理结果
            results = self._process_search_results(response)

            # 计算执行时间
            execution_time = (timezone.now() - start_time).total_seconds()

            # 记录搜索查询
            self._log_search_query(
                user=user,
                query=query,
                search_type=search_type,
                filters=filters or {},
                result_count=response.hits.total.value,
                execution_time=execution_time,
            )

            return {
                "results": results,
                "total": response.hits.total.value,
                "page": page,
                "page_size": page_size,
                "execution_time": execution_time,
                "aggregations": self._process_aggregations(response.aggregations),
            }

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return {
                "results": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "execution_time": 0,
                "error": str(e),
            }

    def _build_search_query(
        self, query: str, search_type: str, filters: Dict, user
    ) -> Search:
        """构建搜索查询"""
        search = Search(index="documents")

        # 构建主查询
        if query:
            if search_type == "full_text":
                # 全文搜索
                main_query = Q(
                    "multi_match",
                    query=query,
                    fields=["title^3", "description^2", "content", "ocr_text"],
                    type="best_fields",
                    fuzziness="AUTO",
                )
            elif search_type == "title":
                # 标题搜索
                main_query = Q("match", title={"query": query, "boost": 2})
            elif search_type == "content":
                # 内容搜索
                main_query = Q("match", content=query)
            else:
                # 默认全文搜索
                main_query = Q(
                    "multi_match",
                    query=query,
                    fields=["title", "description", "content"],
                )
        else:
            main_query = Q("match_all")

        search = search.query(main_query)

        # 添加过滤条件
        filter_queries = []

        # 权限过滤
        if not user.is_staff:
            permission_filter = Q(
                "bool",
                should=[
                    Q("term", uploaded_by__id=user.id),
                    Q("term", is_public=True),
                    # TODO: 添加共享文档过滤
                ],
            )
            filter_queries.append(permission_filter)

        # 状态过滤
        filter_queries.append(Q("term", status="completed"))

        # 应用用户过滤条件
        if filters:
            if "category" in filters:
                filter_queries.append(Q("term", category__id=filters["category"]))

            if "tags" in filters:
                tag_ids = (
                    filters["tags"]
                    if isinstance(filters["tags"], list)
                    else [filters["tags"]]
                )
                filter_queries.append(Q("terms", tags__id=tag_ids))

            if "file_type" in filters:
                filter_queries.append(Q("term", file_type=filters["file_type"]))

            if "date_range" in filters:
                date_range = filters["date_range"]
                if "start" in date_range or "end" in date_range:
                    range_filter = {}
                    if "start" in date_range:
                        range_filter["gte"] = date_range["start"]
                    if "end" in date_range:
                        range_filter["lte"] = date_range["end"]
                    filter_queries.append(Q("range", created_at=range_filter))

            if "file_size_range" in filters:
                size_range = filters["file_size_range"]
                range_filter = {}
                if "min" in size_range:
                    range_filter["gte"] = size_range["min"]
                if "max" in size_range:
                    range_filter["lte"] = size_range["max"]
                filter_queries.append(Q("range", file_size=range_filter))

        # 应用所有过滤条件
        if filter_queries:
            search = search.filter("bool", must=filter_queries)

        # 添加聚合
        search.aggs.bucket("categories", "terms", field="category.name.raw", size=20)
        search.aggs.bucket("tags", "terms", field="tags.name.raw", size=20)
        search.aggs.bucket("file_types", "terms", field="file_type", size=10)
        search.aggs.bucket(
            "upload_dates",
            "date_histogram",
            field="created_at",
            calendar_interval="month",
        )

        # 高亮设置
        search = search.highlight("title", "description", "content", "ocr_text")
        search = search.highlight_options(
            pre_tags=["<mark>"],
            post_tags=["</mark>"],
            fragment_size=150,
            number_of_fragments=3,
        )

        # 排序
        search = search.sort("-_score", "-created_at")

        return search

    def _process_search_results(self, response) -> List[Dict]:
        """处理搜索结果"""
        results = []

        for hit in response:
            result = {
                "id": hit.meta.id,
                "score": hit.meta.score,
                "title": hit.title,
                "description": hit.description,
                "file_type": hit.file_type,
                "file_size": hit.file_size,
                "category": (
                    hit.category.to_dict()
                    if hasattr(hit, "category") and hit.category
                    else None
                ),
                "tags": (
                    [tag.to_dict() for tag in hit.tags] if hasattr(hit, "tags") else []
                ),
                "uploaded_by": (
                    hit.uploaded_by.to_dict() if hasattr(hit, "uploaded_by") else None
                ),
                "created_at": hit.created_at,
                "view_count": hit.view_count,
                "download_count": hit.download_count,
            }

            # 添加高亮信息
            if hasattr(hit.meta, "highlight"):
                result["highlights"] = {}
                for field, highlights in hit.meta.highlight.to_dict().items():
                    result["highlights"][field] = highlights

            results.append(result)

        return results

    def _process_aggregations(self, aggregations) -> Dict:
        """处理聚合结果"""
        if not aggregations:
            return {}

        processed = {}

        for agg_name, agg_data in aggregations.to_dict().items():
            if "buckets" in agg_data:
                processed[agg_name] = [
                    {"key": bucket["key"], "doc_count": bucket["doc_count"]}
                    for bucket in agg_data["buckets"]
                ]

        return processed

    def _log_search_query(
        self,
        user,
        query: str,
        search_type: str,
        filters: Dict,
        result_count: int,
        execution_time: float,
    ):
        """记录搜索查询"""
        try:
            SearchQuery.objects.create(
                user=user,
                query=query,
                search_type=search_type,
                filters=filters,
                result_count=result_count,
                execution_time=execution_time,
            )

            # 更新搜索建议
            self._update_search_suggestions(query)

        except Exception as e:
            logger.error(f"Error logging search query: {str(e)}")

    def _update_search_suggestions(self, query: str):
        """更新搜索建议"""
        try:
            # 清理查询词
            cleaned_query = self._clean_query(query)

            if len(cleaned_query) >= 2:  # 只处理长度大于等于2的查询
                suggestion, created = SearchSuggestion.objects.get_or_create(
                    query=cleaned_query, defaults={"suggestion_type": "popular"}
                )

                if not created:
                    suggestion.frequency += 1
                    suggestion.save(update_fields=["frequency"])

        except Exception as e:
            logger.error(f"Error updating search suggestions: {str(e)}")

    def _clean_query(self, query: str) -> str:
        """清理查询词"""
        # 移除特殊字符，保留中文、英文、数字和空格
        cleaned = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9\s]", " ", query)
        # 移除多余空格
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.lower()

    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """获取搜索建议"""
        try:
            cleaned_query = self._clean_query(query)

            if len(cleaned_query) < 2:
                return []

            # 从数据库获取建议
            suggestions = SearchSuggestion.objects.filter(
                query__icontains=cleaned_query, is_active=True
            ).order_by("-frequency")[:limit]

            return [s.query for s in suggestions]

        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return []

    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """获取热门搜索"""
        try:
            popular = SearchSuggestion.objects.filter(
                suggestion_type="popular", is_active=True
            ).order_by("-frequency")[:limit]

            return [{"query": s.query, "frequency": s.frequency} for s in popular]

        except Exception as e:
            logger.error(f"Error getting popular searches: {str(e)}")
            return []

    def get_user_recent_searches(self, user, limit: int = 10) -> List[str]:
        """获取用户最近搜索"""
        try:
            recent = SearchQuery.objects.filter(user=user).order_by("-created_at")[
                :limit
            ]

            return [q.query for q in recent]

        except Exception as e:
            logger.error(f"Error getting recent searches: {str(e)}")
            return []


def update_search_analytics():
    """更新搜索分析数据"""
    try:
        today = timezone.now().date()

        # 获取今日搜索统计
        today_queries = SearchQuery.objects.filter(created_at__date=today)

        total_searches = today_queries.count()
        unique_users = today_queries.values("user").distinct().count()

        if total_searches > 0:
            avg_results = (
                today_queries.aggregate(avg=Avg("result_count"))["avg"] or 0
            )

            avg_time = (
                today_queries.aggregate(avg=Avg("execution_time"))["avg"] or 0
            )

            # 热门查询
            top_queries = list(
                today_queries.values("query")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )

            # 零结果查询
            zero_result_queries = list(
                today_queries.filter(result_count=0)
                .values("query")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )

            # 创建或更新分析记录
            analytics, created = SearchAnalytics.objects.get_or_create(
                date=today,
                defaults={
                    "total_searches": total_searches,
                    "unique_users": unique_users,
                    "avg_results_per_search": avg_results,
                    "avg_execution_time": avg_time,
                    "top_queries": top_queries,
                    "zero_result_queries": zero_result_queries,
                },
            )

            if not created:
                analytics.total_searches = total_searches
                analytics.unique_users = unique_users
                analytics.avg_results_per_search = avg_results
                analytics.avg_execution_time = avg_time
                analytics.top_queries = top_queries
                analytics.zero_result_queries = zero_result_queries
                analytics.save()

            logger.info(f"Updated search analytics for {today}")

    except Exception as e:
        logger.error(f"Error updating search analytics: {str(e)}")


def rebuild_search_index():
    """重建搜索索引"""
    try:
        from django.core.management import call_command

        call_command("search_index", "--rebuild", "-f")
        logger.info("Search index rebuilt successfully")

    except Exception as e:
        logger.error(f"Error rebuilding search index: {str(e)}")


# 创建全局搜索引擎实例
search_engine = SearchEngine()

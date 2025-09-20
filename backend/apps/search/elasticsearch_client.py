"""
Elasticsearch客户端配置和管理
"""

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearch客户端封装"""

    def __init__(self):
        self.client = None
        self.index_name = getattr(settings, "ELASTICSEARCH_INDEX", "knowledge_base")
        self.connect()

    def connect(self):
        """连接Elasticsearch"""
        try:
            # 新版本Elasticsearch客户端配置
            hosts = (
                getattr(settings, "ELASTICSEARCH_DSL", {})
                .get("default", {})
                .get("hosts", "localhost:9200")
            )

            # 确保URL格式正确
            if not hosts.startswith(("http://", "https://")):
                hosts = f"http://{hosts}"

            self.client = Elasticsearch(
                hosts=[hosts],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True,
            )

            # 测试连接
            if self.client.ping():
                logger.info("Elasticsearch连接成功")
                self.ensure_index_exists()
            else:
                logger.error("Elasticsearch连接失败")

        except ConnectionError as e:
            logger.error(f"Elasticsearch连接错误: {e}")
            self.client = None

    def ensure_index_exists(self):
        """确保索引存在"""
        if not self.client:
            return False

        try:
            if not self.client.indices.exists(index=self.index_name):
                self.create_index()
            return True
        except Exception as e:
            logger.error(f"检查索引失败: {e}")
            return False

    def create_index(self):
        """创建索引"""
        index_mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "ik_smart_analyzer": {
                            "type": "custom",
                            "tokenizer": "ik_smart",
                            "filter": ["lowercase"],
                        },
                        "ik_max_word_analyzer": {
                            "type": "custom",
                            "tokenizer": "ik_max_word",
                            "filter": ["lowercase"],
                        },
                    }
                },
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "analyzer": "ik_smart_analyzer",
                        "search_analyzer": "ik_smart_analyzer",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "ik_max_word_analyzer",
                        "search_analyzer": "ik_smart_analyzer",
                    },
                    "ocr_text": {
                        "type": "text",
                        "analyzer": "ik_max_word_analyzer",
                        "search_analyzer": "ik_smart_analyzer",
                    },
                    "description": {"type": "text", "analyzer": "ik_smart_analyzer"},
                    "file_type": {"type": "keyword"},
                    "file_size": {"type": "long"},
                    "category": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "keyword"},
                        },
                    },
                    "tags": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "keyword"},
                        },
                    },
                    "uploaded_by": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "username": {"type": "keyword"},
                        },
                    },
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "view_count": {"type": "integer"},
                    "download_count": {"type": "integer"},
                    "is_public": {"type": "boolean"},
                }
            },
        }

        try:
            self.client.indices.create(index=self.index_name, body=index_mapping)
            logger.info(f"索引 {self.index_name} 创建成功")
        except Exception as e:
            logger.error(f"创建索引失败: {e}")

    def index_document(self, doc_id: int, document_data: Dict[str, Any]) -> bool:
        """索引单个文档"""
        if not self.client:
            return False

        try:
            response = self.client.index(
                index=self.index_name, id=doc_id, body=document_data
            )
            logger.debug(f"文档 {doc_id} 索引成功: {response['result']}")
            return True
        except Exception as e:
            logger.error(f"索引文档 {doc_id} 失败: {e}")
            return False

    def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """批量索引文档"""
        if not self.client or not documents:
            return False

        try:
            from elasticsearch.helpers import bulk

            actions = []
            for doc in documents:
                action = {"_index": self.index_name, "_id": doc["id"], "_source": doc}
                actions.append(action)

            success, failed = bulk(self.client, actions)
            logger.info(f"批量索引完成: 成功 {success}, 失败 {len(failed)}")
            return len(failed) == 0

        except Exception as e:
            logger.error(f"批量索引失败: {e}")
            return False

    def search_documents(
        self, query: str, filters: Dict = None, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """搜索文档"""
        if not self.client:
            return {"hits": [], "total": 0}

        try:
            # 构建搜索查询
            search_body = self._build_search_query(query, filters, page, size)

            # 执行搜索
            response = self.client.search(index=self.index_name, body=search_body)

            # 格式化结果
            return self._format_search_response(response)

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def _build_search_query(
        self, query: str, filters: Dict = None, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """构建搜索查询"""
        search_body = {
            "from": (page - 1) * size,
            "size": size,
            "query": {"bool": {"must": [], "filter": []}},
            "highlight": {
                "fields": {
                    "title": {
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"],
                        "fragment_size": 100,
                    },
                    "content": {
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"],
                        "fragment_size": 200,
                        "number_of_fragments": 3,
                    },
                    "ocr_text": {
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"],
                        "fragment_size": 200,
                        "number_of_fragments": 2,
                    },
                }
            },
            "sort": [{"_score": {"order": "desc"}}, {"created_at": {"order": "desc"}}],
        }

        # 主查询
        if query.strip():
            search_body["query"]["bool"]["must"].append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "title^3",  # 标题权重最高
                            "content^2",  # 内容权重中等
                            "ocr_text^1.5",  # OCR文本权重较低
                            "description^1",  # 描述权重最低
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                }
            )
        else:
            search_body["query"]["bool"]["must"].append({"match_all": {}})

        # 添加过滤条件
        if filters:
            if filters.get("file_type"):
                search_body["query"]["bool"]["filter"].append(
                    {"term": {"file_type": filters["file_type"]}}
                )

            if filters.get("category_id"):
                search_body["query"]["bool"]["filter"].append(
                    {"term": {"category.id": filters["category_id"]}}
                )

            if filters.get("tags"):
                search_body["query"]["bool"]["filter"].append(
                    {
                        "nested": {
                            "path": "tags",
                            "query": {"terms": {"tags.id": filters["tags"]}},
                        }
                    }
                )

            if filters.get("date_range"):
                date_range = filters["date_range"]
                search_body["query"]["bool"]["filter"].append(
                    {
                        "range": {
                            "created_at": {
                                "gte": date_range.get("start"),
                                "lte": date_range.get("end"),
                            }
                        }
                    }
                )

            if filters.get("is_public") is not None:
                search_body["query"]["bool"]["filter"].append(
                    {"term": {"is_public": filters["is_public"]}}
                )

        return search_body

    def _format_search_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """格式化搜索响应"""
        hits = []

        for hit in response["hits"]["hits"]:
            formatted_hit = {
                "id": hit["_id"],
                "score": hit["_score"],
                "source": hit["_source"],
                "highlight": hit.get("highlight", {}),
            }
            hits.append(formatted_hit)

        return {
            "hits": hits,
            "total": response["hits"]["total"]["value"],
            "max_score": response["hits"]["max_score"],
            "took": response["took"],
        }

    def delete_document(self, doc_id: int) -> bool:
        """删除文档"""
        if not self.client:
            return False

        try:
            response = self.client.delete(index=self.index_name, id=doc_id)
            logger.debug(f"文档 {doc_id} 删除成功: {response['result']}")
            return True
        except NotFoundError:
            logger.warning(f"文档 {doc_id} 不存在")
            return True
        except Exception as e:
            logger.error(f"删除文档 {doc_id} 失败: {e}")
            return False

    def get_search_suggestions(self, query: str, size: int = 5) -> List[str]:
        """获取搜索建议"""
        if not self.client or not query.strip():
            return []

        try:
            search_body = {
                "suggest": {
                    "title_suggest": {
                        "prefix": query,
                        "completion": {"field": "title.suggest", "size": size},
                    }
                }
            }

            response = self.client.search(index=self.index_name, body=search_body)

            suggestions = []
            for option in response["suggest"]["title_suggest"][0]["options"]:
                suggestions.append(option["text"])

            return suggestions

        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}")
            return []

    def get_aggregations(self, field: str, size: int = 10) -> Dict[str, Any]:
        """获取聚合统计"""
        if not self.client:
            return {}

        try:
            search_body = {
                "size": 0,
                "aggs": {f"{field}_stats": {"terms": {"field": field, "size": size}}},
            }

            response = self.client.search(index=self.index_name, body=search_body)

            return response["aggregations"]

        except Exception as e:
            logger.error(f"获取聚合统计失败: {e}")
            return {}


# 全局客户端实例 - 延迟初始化以避免启动错误
es_client = None


def get_es_client():
    """获取Elasticsearch客户端实例"""
    global es_client
    if es_client is None:
        try:
            es_client = ElasticsearchClient()
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Elasticsearch客户端初始化失败: {e}")
            es_client = None
    return es_client

"""
API文档配置
"""

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import status


# 文档管理API文档
document_list_schema = extend_schema(
    summary="获取文档列表",
    description="获取用户可访问的文档列表，支持分页、过滤和搜索",
    parameters=[
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='页码，默认为1'
        ),
        OpenApiParameter(
            name='page_size',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='每页数量，默认为20，最大100'
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='搜索关键词，在标题和描述中搜索'
        ),
        OpenApiParameter(
            name='category',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='文档分类ID'
        ),
        OpenApiParameter(
            name='file_type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='文件类型，如pdf、docx、txt等'
        ),
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='文档状态：pending、processing、processed、error'
        ),
        OpenApiParameter(
            name='created_after',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='创建时间起始日期，格式：YYYY-MM-DD'
        ),
        OpenApiParameter(
            name='created_before',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='创建时间结束日期，格式：YYYY-MM-DD'
        ),
        OpenApiParameter(
            name='ordering',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='排序字段，可选：created_at、updated_at、title、file_size。前缀-表示降序'
        ),
    ],
    responses={
        200: {
            "description": "成功返回文档列表",
            "content": {
                "application/json": {
                    "example": {
                        "count": 100,
                        "next": "http://localhost:8000/api/v1/documents/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "title": "Python编程指南",
                                "description": "详细的Python编程教程",
                                "file_name": "python_guide.pdf",
                                "file_size": 2048576,
                                "file_type": "pdf",
                                "status": "processed",
                                "category": {
                                    "id": 1,
                                    "name": "技术文档"
                                },
                                "tags": [
                                    {"id": 1, "name": "Python"},
                                    {"id": 2, "name": "编程"}
                                ],
                                "uploaded_by": {
                                    "id": 1,
                                    "username": "admin",
                                    "email": "admin@example.com"
                                },
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T10:35:00Z",
                                "download_count": 25,
                                "view_count": 150
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "未授权访问"},
        403: {"description": "权限不足"},
        500: {"description": "服务器内部错误"}
    },
    tags=['文档管理']
)

document_create_schema = extend_schema(
    summary="创建文档",
    description="创建新的文档记录（不包含文件上传）",
    request={
        "application/json": {
            "example": {
                "title": "新文档标题",
                "description": "文档描述信息",
                "category": 1,
                "tags": [1, 2, 3],
                "is_public": True,
                "metadata": {
                    "author": "张三",
                    "version": "1.0"
                }
            }
        }
    },
    responses={
        201: {
            "description": "文档创建成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "新文档标题",
                        "description": "文档描述信息",
                        "status": "pending",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        401: {"description": "未授权访问"},
        500: {"description": "服务器内部错误"}
    },
    tags=['文档管理']
)

document_upload_schema = extend_schema(
    summary="上传文档文件",
    description="上传文档文件并创建文档记录，支持PDF、DOC、DOCX、TXT格式，最大50MB",
    request={
        "multipart/form-data": {
            "example": {
                "title": "上传文档标题",
                "description": "文档描述",
                "category": 1,
                "file": "binary_file_data",
                "tags": [1, 2],
                "is_public": False
            }
        }
    },
    responses={
        201: {
            "description": "文件上传成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "上传文档标题",
                        "file_name": "document.pdf",
                        "file_size": 1024576,
                        "file_type": "pdf",
                        "status": "processing",
                        "task_id": "celery-task-id-12345",
                        "message": "文件上传成功，正在处理中..."
                    }
                }
            }
        },
        400: {"description": "文件格式不支持或文件过大"},
        401: {"description": "未授权访问"},
        413: {"description": "文件大小超过限制"},
        500: {"description": "服务器内部错误"}
    },
    tags=['文档管理']
)

# 搜索API文档
search_schema = extend_schema(
    summary="文档搜索",
    description="全文搜索文档内容，支持关键词高亮、相关性排序和分页",
    request={
        "application/json": {
            "example": {
                "query": "Python编程",
                "filters": {
                    "category": 1,
                    "file_type": "pdf",
                    "created_after": "2024-01-01",
                    "created_before": "2024-12-31"
                },
                "sort_by": "relevance",
                "sort_order": "desc",
                "page": 1,
                "page_size": 20,
                "highlight": True
            }
        }
    },
    responses={
        200: {
            "description": "搜索成功",
            "content": {
                "application/json": {
                    "example": {
                        "query": "Python编程",
                        "total_count": 25,
                        "page": 1,
                        "page_size": 20,
                        "total_pages": 2,
                        "took": 45,
                        "results": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "title": "Python编程指南",
                                "description": "详细的<mark>Python编程</mark>教程",
                                "content_snippet": "这是一个关于<mark>Python编程</mark>的详细教程...",
                                "file_type": "pdf",
                                "category": "技术文档",
                                "score": 0.95,
                                "created_at": "2024-01-15T10:30:00Z",
                                "highlights": {
                                    "title": ["<mark>Python编程</mark>指南"],
                                    "content": ["关于<mark>Python编程</mark>的教程"]
                                }
                            }
                        ],
                        "aggregations": {
                            "categories": [
                                {"key": "技术文档", "doc_count": 15},
                                {"key": "教程", "doc_count": 10}
                            ],
                            "file_types": [
                                {"key": "pdf", "doc_count": 20},
                                {"key": "docx", "doc_count": 5}
                            ]
                        }
                    }
                }
            }
        },
        400: {"description": "搜索参数错误"},
        401: {"description": "未授权访问"},
        500: {"description": "搜索服务错误"}
    },
    tags=['搜索功能']
)

search_suggestions_schema = extend_schema(
    summary="搜索建议",
    description="根据输入的关键词获取搜索建议",
    parameters=[
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='搜索关键词前缀',
            required=True
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='返回建议数量，默认10，最大50'
        ),
    ],
    responses={
        200: {
            "description": "获取建议成功",
            "content": {
                "application/json": {
                    "example": {
                        "query": "Py",
                        "suggestions": [
                            {
                                "text": "Python编程",
                                "frequency": 150,
                                "type": "history"
                            },
                            {
                                "text": "Python框架",
                                "frequency": 89,
                                "type": "popular"
                            },
                            {
                                "text": "PyTorch教程",
                                "frequency": 67,
                                "type": "completion"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "参数错误"},
        401: {"description": "未授权访问"}
    },
    tags=['搜索功能']
)

# 监控API文档
monitoring_metrics_schema = extend_schema(
    summary="获取系统指标",
    description="获取系统性能指标数据",
    parameters=[
        OpenApiParameter(
            name='metric_type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='指标类型：system、application、custom'
        ),
        OpenApiParameter(
            name='time_range',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='时间范围：1h、6h、24h、7d、30d'
        ),
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='数据间隔：1m、5m、15m、1h、1d'
        ),
    ],
    responses={
        200: {
            "description": "获取指标成功",
            "content": {
                "application/json": {
                    "example": {
                        "time_range": "24h",
                        "interval": "1h",
                        "metrics": {
                            "system": {
                                "cpu_usage": [
                                    {"timestamp": "2024-01-15T10:00:00Z", "value": 45.2},
                                    {"timestamp": "2024-01-15T11:00:00Z", "value": 52.1}
                                ],
                                "memory_usage": [
                                    {"timestamp": "2024-01-15T10:00:00Z", "value": 68.5},
                                    {"timestamp": "2024-01-15T11:00:00Z", "value": 71.3}
                                ]
                            },
                            "application": {
                                "active_users": [
                                    {"timestamp": "2024-01-15T10:00:00Z", "value": 25},
                                    {"timestamp": "2024-01-15T11:00:00Z", "value": 32}
                                ],
                                "document_uploads": [
                                    {"timestamp": "2024-01-15T10:00:00Z", "value": 5},
                                    {"timestamp": "2024-01-15T11:00:00Z", "value": 8}
                                ]
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "未授权访问"},
        403: {"description": "权限不足"}
    },
    tags=['系统监控']
)

# 用户认证API文档
auth_login_schema = extend_schema(
    summary="用户登录",
    description="用户登录获取JWT访问令牌",
    request={
        "application/json": {
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }
    },
    responses={
        200: {
            "description": "登录成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "Bearer",
                        "expires_in": 3600,
                        "user": {
                            "id": 1,
                            "username": "admin",
                            "email": "admin@example.com",
                            "first_name": "管理员",
                            "last_name": "",
                            "is_staff": True,
                            "is_superuser": True,
                            "date_joined": "2024-01-01T00:00:00Z"
                        }
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        401: {"description": "用户名或密码错误"},
        429: {"description": "登录尝试过于频繁"}
    },
    tags=['用户认证']
)

auth_refresh_schema = extend_schema(
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌",
    request={
        "application/json": {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }
    },
    responses={
        200: {
            "description": "令牌刷新成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "Bearer",
                        "expires_in": 3600
                    }
                }
            }
        },
        400: {"description": "刷新令牌无效"},
        401: {"description": "刷新令牌已过期"}
    },
    tags=['用户认证']
)

# 错误响应示例
error_responses = {
    400: {
        "description": "请求参数错误",
        "content": {
            "application/json": {
                "example": {
                    "error": "validation_error",
                    "message": "请求参数验证失败",
                    "details": {
                        "field_name": ["此字段是必需的"]
                    },
                    "timestamp": "2024-01-15T10:30:00Z",
                    "path": "/api/v1/documents/"
                }
            }
        }
    },
    401: {
        "description": "未授权访问",
        "content": {
            "application/json": {
                "example": {
                    "error": "authentication_required",
                    "message": "需要提供有效的认证凭据",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "path": "/api/v1/documents/"
                }
            }
        }
    },
    403: {
        "description": "权限不足",
        "content": {
            "application/json": {
                "example": {
                    "error": "permission_denied",
                    "message": "您没有执行此操作的权限",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "path": "/api/v1/documents/"
                }
            }
        }
    },
    404: {
        "description": "资源不存在",
        "content": {
            "application/json": {
                "example": {
                    "error": "not_found",
                    "message": "请求的资源不存在",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "path": "/api/v1/documents/123/"
                }
            }
        }
    },
    500: {
        "description": "服务器内部错误",
        "content": {
            "application/json": {
                "example": {
                    "error": "internal_server_error",
                    "message": "服务器内部错误，请稍后重试",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "path": "/api/v1/documents/"
                }
            }
        }
    }
}
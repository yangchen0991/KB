
from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os

@csrf_exempt
def serve_static_file(request, path):
    """直接服务静态文件"""
    static_root = settings.STATIC_ROOT
    file_path = os.path.join(static_root, path)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        raise Http404("Static file not found")

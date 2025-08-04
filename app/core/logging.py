import json
import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# 配置一个基础的 logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:

        request_id = str(int(time.time() * 1000))  # 简单生成请求ID
        start_time = time.time()

        # --- 1. 记录请求信息 ---
        request_log_data = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers.items()),
        }

        # !! 警告：记录 body 可能会暴露敏感信息并影响性能 !!
        # 仅在调试需要时开启，并确保过滤敏感数据
        # content_type = request.headers.get("content-type")
        # if content_type and "application/json" in content_type:
        #     try:
        #         request_body = await request.json()
        #         request_log_data["body"] = request_body
        #     except json.JSONDecodeError:
        #         request_log_data["body"] = (await request.body()).decode('utf-8')

        logger.info(f"Request[{request_id}]: {json.dumps(request_log_data, indent=2)}")

        # --- 2. 处理请求并获取响应 ---
        response = await call_next(request)
        process_time = time.time() - start_time

        # --- 3. 记录响应信息 ---
        response_log_data = {
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "headers": dict(response.headers.items()),
        }

        # !! 警告：同样，记录响应 body 也有风险 !!
        # 且读取响应流后需要重新构建它，会增加开销
        # response_body = b""
        # async for chunk in response.body_iterator:
        #     response_body += chunk
        # if response_body:
        #     try:
        #          # 尝试以JSON格式记录
        #         response_log_data["body"] = json.loads(response_body)
        #     except json.JSONDecodeError:
        #         # 如果不是JSON，则以字符串形式记录
        #         response_log_data["body"] = response_body.decode('utf-8')

        # # 由于我们读取了 body_iterator，需要返回一个新的 Response
        # # 如果不记录 body，则可以直接 return response
        # return Response(
        #     content=response_body,
        #     status_code=response.status_code,
        #     headers=dict(response.headers),
        #     media_type=response.media_type
        # )

        logger.info(
            f"Response[{request_id}]: {json.dumps(response_log_data, indent=2)}",
        )

        return response

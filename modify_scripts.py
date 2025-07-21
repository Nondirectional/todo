from mitmproxy import http
import urllib.parse

# 配置常量，方便后期修改
TARGET_VERSION = "2025100"
TARGET_USER_ID = "6bwb0pvs0dl3p6qjxisr8nwmn"

def modify_query_param(url: str, param: str, new_value: str) -> str:
    """ 修改 URL 查询参数 """
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    if param in query_params:
        old_value = query_params[param][0]
        query_params[param] = [new_value]
        print(f"修改 {param}: {old_value} -> {new_value}")

    # 重新构造 URL
    new_query = urllib.parse.urlencode(query_params, doseq=True)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"

def request(flow: http.HTTPFlow) -> None:
    """ 拦截指定 URL 并修改参数 """
    url = flow.request.pretty_url

    if "/lservice/rpc/obtainTrial.action" in url:
        print(f"拦截请求: {url}")
        flow.request.url = modify_query_param(flow.request.url, "version", TARGET_VERSION)
        print(f"修改后的 URL: {flow.request.url}")

    elif "/lservice/rpc/obtainLicense.action" in url:
        print(f"拦截请求: {url}")
        flow.request.url = modify_query_param(flow.request.url, "userId", TARGET_USER_ID)
        print(f"修改后的 URL: {flow.request.url}")

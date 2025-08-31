import os
import yaml
import requests
import base64
import re

# ===============================================
# 本脚本是专为处理Clash订阅设计的终极版本
# 最终修正：移除 expire_str 字段，确保与OpenClash等客户端完美兼容
# ===============================================

# --- 配置区 ---
SUB_URL_ENV = os.environ.get("SUB_URL")
CUSTOM_RULES_PATH = "my_rules.yaml"
OUTPUT_CONFIG_PATH = "config.yaml"
HEADERS = {'User-Agent': 'Clash/2023.08.17 Premium'}

# --- 函数区 ---
def parse_subscription_userinfo(header_str):
    """从Subscription-Userinfo头中解析标准的流量和到期时间信息"""
    if not header_str:
        return None
    
    # 只匹配 upload, download, total, expire 这四个标准字段
    upload = re.search(r'upload=([\d.]+)', header_str)
    download = re.search(r'download=([\d.]+)', header_str)
    total = re.search(r'total=([\d.]+)', header_str)
    expire = re.search(r'expire=(\d+)', header_str)

    # 如果关键字段缺失，则返回None
    if not all([upload, download, total, expire]):
        return None

    info = {
        'upload': int(float(upload.group(1))),
        'download': int(float(download.group(1))),
        'total': int(float(total.group(1))),
        'expire': int(expire.group(1))
    }
    
    return info

# --- 主程序 ---
def main():
    print(">> 开始处理订阅...")

    if not SUB_URL_ENV:
        print("!! 错误：没有在环境变量中找到 SUB_URL！")
        exit(1)

    try:
        print("   正在以Clash客户端名义下载订阅内容...")
        response = requests.get(SUB_URL_ENV, headers=HEADERS)
        response.raise_for_status()
        response.encoding = 'utf-8'
        sub_content_raw = response.text
        
        userinfo_header = None
        for key, value in response.headers.items():
            if key.lower() == 'subscription-userinfo':
                userinfo_header = value
                break
        
        sub_info = parse_subscription_userinfo(userinfo_header)
        if sub_info:
            print(f"   成功提取到标准订阅信息: {sub_info}")
        else:
            print("   警告: 未在响应头中找到有效的订阅信息。")

        content_to_parse = ""
        try:
            content_to_parse = base64.b64decode(sub_content_raw).decode('utf-8')
            print("   订阅内容被识别为Base64，已成功解码。")
        except Exception:
            print("   无法作为Base64解码，将直接作为纯文本YAML处理。")
            content_to_parse = sub_content_raw

        config_data = yaml.safe_load(content_to_parse)
        
        if not isinstance(config_data, dict):
            print("!! 错误：最终解析后的订阅内容不是一个有效的配置字典（dict）。")
            exit(1)
        print("   订阅文件下载并解析成功。")
        
        if sub_info:
            config_data['subscription-userinfo'] = sub_info
            print("   已将标准订阅信息添加到新的配置文件中。")

        print(f"   正在读取自定义规则文件: {CUSTOM_RULES_PATH}")
        with open(CUSTOM_RULES_PATH, 'r', encoding='utf-8') as f:
            custom_rules_data = yaml.safe_load(f)
        
        if 'rules' in custom_rules_data and isinstance(custom_rules_data['rules'], list):
            if 'rules' not in config_data or not isinstance(config_data.get('rules'), list):
                config_data['rules'] = []
            
            custom_rule_count = len(custom_rules_data['rules'])
            config_data['rules'] = custom_rules_data['rules'] + config_data['rules']
            print(f"   规则合并完成。添加了 {custom_rule_count} 条自定义规则。")
        else:
            print("   警告：自定义规则文件中没有找到有效的'rules'列表。")

        print(f"   正在将最终配置写入到: {OUTPUT_CONFIG_PATH}")
        with open(OUTPUT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
            
        print(">> 处理完成，新的配置文件已生成！")

    except Exception as e:
        print(f"!! 发生未知错误: {e}")
        exit(1)

if __name__ == '__main__':
    main()

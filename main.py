import os
import yaml
import requests
import base64
import re
from datetime import datetime

# ===============================================
# 本脚本是专为处理Clash订阅设计的终极版本
# 新增功能：打印所有响应头，用于最终诊断
# ===============================================

# --- 配置区 ---
SUB_URL_ENV = os.environ.get("SUB_URL")
CUSTOM_RULES_PATH = "my_rules.yaml"
OUTPUT_CONFIG_PATH = "config.yaml"
HEADERS = {'User-Agent': 'Clash/2023.08.17 Premium'}

# --- 函数区 ---
def parse_subscription_userinfo(header_str):
    """从Subscription-Userinfo头中解析流量和到期时间信息"""
    if not header_str:
        return None
    
    pairs = re.findall(r'(\w+)=([\d.]+)', header_str)
    info = {key: int(float(value)) for key, value in pairs}
    
    expire_match = re.search(r'expire=(\d+)', header_str)
    if expire_match:
        expire_timestamp = int(expire_match.group(1))
        info['expire_str'] = datetime.fromtimestamp(expire_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        info['expire'] = expire_timestamp
        
    return info if info else None

# --- 主程序 ---
def main():
    print(">> 开始处理订阅...")

    if not SUB_URL_ENV:
        print("!! 错误：没有在环境变量中找到 SUB_URL！")
        exit(1)

    try:
        # 1. 下载原始订阅文件
        print("   正在以Clash客户端名义下载订阅内容...")
        response = requests.get(SUB_URL_ENV, headers=HEADERS)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        # ===============================================================
        # VVVV  【核心诊断代码】打印所有收到的响应头  VVVV
        print("\n   --- 服务器响应头信息 ---")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        print("   ------------------------\n")
        # ^^^^  【诊断代码结束】  ^^^^
        # ===============================================================

        sub_content_raw = response.text
        
        # 2. 提取并解析Subscription-Userinfo头 (不区分大小写)
        userinfo_header = None
        for key, value in response.headers.items():
            if key.lower() == 'subscription-userinfo':
                userinfo_header = value
                break
        
        sub_info = parse_subscription_userinfo(userinfo_header)
        if sub_info:
            print(f"   成功提取到订阅信息: {sub_info}")
        else:
            print("   警告: 未在响应头中找到有效的'Subscription-Userinfo'。")

        # ... (后续代码与上一版完全相同，这里省略以便清晰)
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
            print("   已将订阅信息添加到新的配置文件中。")

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

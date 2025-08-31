import os
import yaml
import requests
import base64

# 从环境变量中获取订阅链接
sub_url = os.environ.get("SUB_URL")
# 自定义规则文件的路径
custom_rules_path = "my_rules.yaml"
# 最终生成的配置文件路径
output_config_path = "config.yaml"

# 伪装成Clash客户端的请求头
headers = {
    'User-Agent': 'Clash/2023.08.17 Premium'
}

print("开始处理订阅...")

if not sub_url:
    print("错误：没有在环境变量中找到 SUB_URL！")
    exit(1)

try:
    # 1. 下载原始订阅文件
    print(f"正在以Clash客户端名义从订阅链接下载内容...")
    response = requests.get(sub_url, headers=headers)
    response.raise_for_status()
    # 确保使用UTF-8编码处理响应内容
    response.encoding = 'utf-8'
    sub_content_raw = response.text
    
    # 2. 智能判断和处理内容
    content_to_parse = ""
    try:
        # 尝试进行Base64解码
        decoded_bytes = base64.b64decode(sub_content_raw)
        content_to_parse = decoded_bytes.decode('utf-8')
        print("订阅内容被识别为Base64，已成功解码。")
    except Exception:
        # 如果解码失败，则直接使用原始内容
        print("无法作为Base64解码，将直接作为纯文本YAML处理。")
        content_to_parse = sub_content_raw

    # 3. 解析最终的YAML内容
    config_data = yaml.safe_load(content_to_parse)
        
    # 4. 关键检查：确保解析结果是一个字典
    if not isinstance(config_data, dict):
        print(f"错误：最终解析后的订阅内容不是一个有效的配置字典（dict）。")
        print(f"获取到的内容开头: {content_to_parse[:250]}")
        exit(1)
        
    print("订阅文件下载并解析成功。")

    # 5. 读取并合并自定义规则
    print(f"正在读取自定义规则文件: {custom_rules_path}")
    with open(custom_rules_path, 'r', encoding='utf-8') as f:
        custom_rules_data = yaml.safe_load(f)
    
    if 'rules' in custom_rules_data and isinstance(custom_rules_data['rules'], list):
        print("自定义规则读取成功。")
        if 'rules' not in config_data or not config_data['rules']:
            config_data['rules'] = []
        
        custom_rule_count = len(custom_rules_data['rules'])
        config_data['rules'] = custom_rules_data['rules'] + config_data['rules']
        print(f"规则合并完成。添加了 {custom_rule_count} 条自定义规则。")
    else:
        print("警告：自定义规则文件中没有找到有效的'rules'列表。")

    # 6. 写入最终的配置文件
    print(f"正在将最终配置写入到: {output_config_path}")
    with open(output_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
        
    print("处理完成，新的配置文件已生成！")

except Exception as e:
    print(f"发生未知错误: {e}")
    exit(1)

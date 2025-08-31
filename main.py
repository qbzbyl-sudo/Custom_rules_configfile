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
    # 1. 下载原始订阅文件（重要：带上伪装的请求头）
    print(f"正在以Clash客户端名义从订阅链接下载内容...")
    response = requests.get(sub_url, headers=headers)
    response.raise_for_status()
    
    # 获取原始内容
    sub_content_raw = response.text
    
    # 2. 尝试Base64解码
    try:
        decoded_content = base64.b64decode(sub_content_raw).decode('utf-8')
        config_data = yaml.safe_load(decoded_content)
        print("订阅内容被识别为Base64，已成功解码并解析。")
    except (base64.binascii.Error, UnicodeDecodeError, yaml.YAMLError):
        print("订阅内容不是有效的Base64或解码后非YAML，将尝试作为纯文本YAML解析。")
        config_data = yaml.safe_load(sub_content_raw)

    # 3. 关键检查：确保解析结果是一个字典
    if not isinstance(config_data, dict):
        print(f"错误：最终解析后的订阅内容不是一个有效的配置字典（dict）。请确认订阅链接是Clash专用格式。")
        print(f"获取到的内容开头: {sub_content_raw[:200]}")
        exit(1)
        
    print("订阅文件下载并解析成功。")

    # 4. 读取自定义规则文件
    print(f"正在读取自定义规则文件: {custom_rules_path}")
    with open(custom_rules_path, 'r', encoding='utf-8') as f:
        custom_rules_data = yaml.safe_load(f)
    
    if 'rules' in custom_rules_data and custom_rules_data['rules']:
        print("自定义规则读取成功。")
        # 5. 合并规则
        if 'rules' not in config_data or not config_data['rules']:
            config_data['rules'] = []
            
        custom_rule_count = len(custom_rules_data['rules'])
        config_data['rules'] = custom_rules_data['rules'] + config_data['rules']
        print(f"规则合并完成。添加了 {custom_rule_count} 条自定义规则。")
    else:
        print("警告：自定义规则文件中没有找到有效的'rules'。")

    # 6. 写入最终的配置文件
    print(f"正在将最终配置写入到: {output_config_path}")
    with open(output_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
        
    print("处理完成，新的配置文件已生成！")

except Exception as e:
    print(f"发生未知错误: {e}")
    exit(1)

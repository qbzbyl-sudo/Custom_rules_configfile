import os
import yaml
import requests

# 从环境变量中获取订阅链接，这样更安全
sub_url = os.environ.get("SUB_URL")
# 自定义规则文件的路径
custom_rules_path = "my_rules.yaml"
# 最终生成的配置文件路径
output_config_path = "config.yaml"

print("开始处理订阅...")

if not sub_url:
    print("错误：没有在环境变量中找到 SUB_URL！")
    exit(1)

try:
    # 1. 下载原始订阅文件
    print(f"正在从 {sub_url[:30]}... 下载订阅文件...")
    response = requests.get(sub_url)
    response.raise_for_status() # 如果请求失败则抛出异常
    
    # 使用UTF-8编码读取内容
    response.encoding = 'utf-8'
    sub_content = response.text
    
    # 将下载的内容解析为YAML对象
    config_data = yaml.safe_load(sub_content)
    print("订阅文件下载并解析成功。")

    # 2. 读取自定义规则文件
    print(f"正在读取自定义规则文件: {custom_rules_path}")
    with open(custom_rules_path, 'r', encoding='utf-8') as f:
        custom_rules_data = yaml.safe_load(f)
    
    if 'rules' in custom_rules_data and custom_rules_data['rules']:
        print("自定义规则读取成功。")
        # 3. 合并规则 (将自定义规则放在最前面，使其优先级最高)
        # 确保原始配置中存在 'rules' 键
        if 'rules' not in config_data or not config_data['rules']:
            config_data['rules'] = []
            
        original_rule_count = len(config_data['rules'])
        custom_rule_count = len(custom_rules_data['rules'])
        
        config_data['rules'] = custom_rules_data['rules'] + config_data['rules']
        print(f"规则合并完成。添加了 {custom_rule_count} 条自定义规则，总规则数: {len(config_data['rules'])}。")
    else:
        print("警告：自定义规则文件中没有找到有效的'rules'。")

    # 4. 写入最终的配置文件
    print(f"正在将最终配置写入到: {output_config_path}")
    with open(output_config_path, 'w', encoding='utf-8') as f:
        # allow_unicode=True 保证中文字符正常显示
        yaml.dump(config_data, f, allow_unicode=True)
        
    print("处理完成，新的配置文件已生成！")

except requests.exceptions.RequestException as e:
    print(f"下载订阅时发生网络错误: {e}")
    exit(1)
except yaml.YAMLError as e:
    print(f"解析YAML时发生错误: {e}")
    exit(1)
except Exception as e:
    print(f"发生未知错误: {e}")
    exit(1)

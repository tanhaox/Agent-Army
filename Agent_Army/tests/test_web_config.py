"""
测试Web配置接口功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_save_api_key():
    """测试API密钥保存功能"""
    print("\n" + "="*60)
    print("测试API密钥保存功能")
    print("="*60)

    # 模拟web_app中的保存函数
    def save_api_key_to_config(api_name: str, api_key: str):
        """保存API密钥到配置文件"""
        import yaml

        # 读取配置文件
        config_path = project_root / "config" / "api_keys.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        # 更新配置
        if api_name not in config:
            config[api_name] = {}

        config[api_name]["api_key"] = f"${{{api_name.upper()}_API_KEY}}"

        # 写回文件
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

        # 更新环境变量（当前会话）
        os.environ[f"{api_name.upper()}_API_KEY"] = api_key

        # 保存到.env文件（持久化）
        env_path = project_root / ".env"
        if not env_path.exists():
            # 创建.env文件
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write("# Agent Army - 环境变量配置\n\n")

        # 读取.env文件
        with open(env_path, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()

        # 更新或添加API密钥
        key_name = f"{api_name.upper()}_API_KEY"
        updated = False
        new_lines = []

        for line in env_lines:
            if line.startswith(f"{key_name}="):
                new_lines.append(f"{key_name}={api_key}\n")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f"{key_name}={api_key}\n")

        # 写回.env文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        return True

    # 测试1: 保存智谱AI密钥
    print("\n测试1: 保存智谱AI密钥")
    try:
        result = save_api_key_to_config("zhipu", "test_zhipu_key_12345")
        if result:
            print("✅ 智谱AI密钥保存成功")
        else:
            print("❌ 智谱AI密钥保存失败")
    except Exception as e:
        print(f"❌ 保存失败: {str(e)}")

    # 测试2: 保存Tushare密钥
    print("\n测试2: 保存Tushare密钥")
    try:
        result = save_api_key_to_config("tushare", "test_tushare_key_67890")
        if result:
            print("✅ Tushare密钥保存成功")
        else:
            print("❌ Tushare密钥保存失败")
    except Exception as e:
        print(f"❌ 保存失败: {str(e)}")

    # 测试3: 验证环境变量
    print("\n测试3: 验证环境变量")
    zhipu_key = os.getenv("ZHIPU_API_KEY", "")
    tushare_key = os.getenv("TUSHARE_API_KEY", "")

    if zhipu_key == "test_zhipu_key_12345":
        print("✅ ZHIPU_API_KEY环境变量正确")
    else:
        print(f"❌ ZHIPU_API_KEY环境变量错误: {zhipu_key}")

    if tushare_key == "test_tushare_key_67890":
        print("✅ TUSHARE_API_KEY环境变量正确")
    else:
        print(f"❌ TUSHARE_API_KEY环境变量错误: {tushare_key}")

    # 测试4: 验证.env文件
    print("\n测试4: 验证.env文件")
    env_path = project_root / ".env"
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()

        if "ZHIPU_API_KEY=test_zhipu_key_12345" in env_content:
            print("✅ .env文件包含智谱AI密钥")
        else:
            print("❌ .env文件缺少智谱AI密钥")

        if "TUSHARE_API_KEY=test_tushare_key_67890" in env_content:
            print("✅ .env文件包含Tushare密钥")
        else:
            print("❌ .env文件缺少Tushare密钥")
    else:
        print("❌ .env文件不存在")

def test_config_yaml():
    """测试配置文件YAML格式"""
    print("\n" + "="*60)
    print("测试配置文件YAML格式")
    print("="*60)

    import yaml

    config_path = project_root / "config" / "api_keys.yaml"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print("✅ YAML格式正确")
        print(f"✅ 配置项数量: {len(config)}")

        # 检查关键配置
        if "zhipu" in config:
            print("✅ 包含智谱AI配置")
        else:
            print("❌ 缺少智谱AI配置")

        if "tushare" in config:
            print("✅ 包含Tushare配置")
        else:
            print("⚠️ 缺少Tushare配置（正常，刚添加）")

    except Exception as e:
        print(f"❌ YAML格式错误: {str(e)}")

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  Web配置接口功能测试")
    print("="*60)

    # 测试1: API密钥保存
    test_save_api_key()

    # 测试2: YAML配置
    test_config_yaml()

    print("\n" + "="*60)
    print("  测试完成")
    print("="*60)

if __name__ == "__main__":
    main()

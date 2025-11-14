"""
测试配置加载器模块
"""

import os
import pytest
from unittest.mock import patch, mock_open
from rag5.config.loader import ConfigLoader


def test_config_loader_initialization():
    """测试ConfigLoader初始化"""
    loader = ConfigLoader()
    assert loader is not None


def test_get_env_with_default():
    """测试获取环境变量（使用默认值）"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {}, clear=True):
        value = loader.get_env('NONEXISTENT_VAR', 'default_value')
        assert value == 'default_value'


def test_get_env_from_environment():
    """测试从环境变量获取值"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {'TEST_VAR': 'test_value'}, clear=True):
        value = loader.get_env('TEST_VAR', 'default')
        assert value == 'test_value'


def test_get_env_no_default():
    """测试获取不存在的环境变量（无默认值）"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {}, clear=True):
        value = loader.get_env('NONEXISTENT_VAR')
        assert value is None


def test_load_env_file_success():
    """测试成功加载.env文件"""
    loader = ConfigLoader()

    env_content = """
# 注释行
OLLAMA_HOST=http://test:11434
LLM_MODEL=test-model
EMPTY_VALUE=

# 另一个注释
QDRANT_URL=http://test:6333
"""

    with patch('builtins.open', mock_open(read_data=env_content)):
        with patch('os.path.exists', return_value=True):
            result = loader.load_env_file('.env')

            assert result['OLLAMA_HOST'] == 'http://test:11434'
            assert result['LLM_MODEL'] == 'test-model'
            assert result['QDRANT_URL'] == 'http://test:6333'
            assert 'EMPTY_VALUE' not in result  # 空值应该被忽略


def test_load_env_file_not_found():
    """测试加载不存在的.env文件"""
    loader = ConfigLoader()

    with patch('os.path.exists', return_value=False):
        result = loader.load_env_file('nonexistent.env')
        assert result == {}


def test_load_env_file_with_quotes():
    """测试加载包含引号的.env文件"""
    loader = ConfigLoader()

    env_content = """
QUOTED_VALUE="value with spaces"
SINGLE_QUOTED='single quoted'
"""

    with patch('builtins.open', mock_open(read_data=env_content)):
        with patch('os.path.exists', return_value=True):
            result = loader.load_env_file('.env')

            assert result['QUOTED_VALUE'] == 'value with spaces'
            assert result['SINGLE_QUOTED'] == 'single quoted'


def test_load_env_file_malformed_lines():
    """测试处理格式错误的行"""
    loader = ConfigLoader()

    env_content = """
VALID_VAR=value
INVALID_LINE_NO_EQUALS
=NO_KEY
ANOTHER_VALID=another_value
"""

    with patch('builtins.open', mock_open(read_data=env_content)):
        with patch('os.path.exists', return_value=True):
            result = loader.load_env_file('.env')

            assert result['VALID_VAR'] == 'value'
            assert result['ANOTHER_VALID'] == 'another_value'
            assert 'INVALID_LINE_NO_EQUALS' not in result


def test_get_int_valid():
    """测试获取整数值"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {'INT_VAR': '42'}, clear=True):
        value = loader.get_int('INT_VAR', 10)
        assert value == 42
        assert isinstance(value, int)


def test_get_int_invalid():
    """测试获取无效整数值（返回默认值）"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {'INT_VAR': 'not_a_number'}, clear=True):
        value = loader.get_int('INT_VAR', 10)
        assert value == 10


def test_get_int_missing():
    """测试获取不存在的整数值"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {}, clear=True):
        value = loader.get_int('MISSING_VAR', 10)
        assert value == 10


def test_get_float_valid():
    """测试获取浮点数值"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {'FLOAT_VAR': '3.14'}, clear=True):
        value = loader.get_float('FLOAT_VAR', 1.0)
        assert value == 3.14
        assert isinstance(value, float)


def test_get_float_invalid():
    """测试获取无效浮点数值（返回默认值）"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {'FLOAT_VAR': 'not_a_float'}, clear=True):
        value = loader.get_float('FLOAT_VAR', 1.0)
        assert value == 1.0


def test_get_bool_true_values():
    """测试获取布尔值（真值）"""
    loader = ConfigLoader()

    true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES']

    for true_val in true_values:
        with patch.dict(os.environ, {'BOOL_VAR': true_val}, clear=True):
            value = loader.get_bool('BOOL_VAR', False)
            assert value is True, f"Failed for value: {true_val}"


def test_get_bool_false_values():
    """测试获取布尔值（假值）"""
    loader = ConfigLoader()

    false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO']

    for false_val in false_values:
        with patch.dict(os.environ, {'BOOL_VAR': false_val}, clear=True):
            value = loader.get_bool('BOOL_VAR', True)
            assert value is False, f"Failed for value: {false_val}"


def test_get_bool_default():
    """测试获取不存在的布尔值（返回默认值）"""
    loader = ConfigLoader()

    with patch.dict(os.environ, {}, clear=True):
        value = loader.get_bool('MISSING_VAR', True)
        assert value is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

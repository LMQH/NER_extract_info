"""
文本预处理模块
使用qwen-flash大模型对输入文本进行错字纠错和地址信息补全
"""
import os
import json
import re
import logging
from typing import Dict, Any, Optional
from dashscope import Generation
from src.config.constants import ADDRESS_KEYWORDS, PHONE_PATTERN, FIXED_PHONE_PATTERN, CHINESE_NAME_PATTERN
from src.utils.exceptions import NERDemoException

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """文本预处理器，使用qwen-flash模型进行文本纠错和地址补全"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化文本预处理器
        
        Args:
            api_key: DashScope API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise NERDemoException("未找到DASHSCOPE_API_KEY，请在环境配置文件中设置")
        
        # 设置API密钥
        os.environ['DASHSCOPE_API_KEY'] = self.api_key
        
        self.model_name = 'qwen-flash'
    
    def preprocess(self, text: str) -> Dict[str, Any]:
        """
        对输入文本进行预处理（错字纠错和地址补全）
        
        Args:
            text: 输入文本，格式：地址信息 人名 电话
            
        Returns:
            预处理结果字典，包含:
            - original_text: 原始文本
            - corrected_text: 处理后的完整文本（地址 人名 电话）
            - address_info: 补全的地址信息
            - error: 错误信息（如果有）
        """
        if not text or not text.strip():
            return {
                "original_text": text,
                "corrected_text": text,
                "address_info": {},
                "error": "输入文本为空"
            }
        
        try:
            # 步骤1: 提取人名、电话和地址
            extracted = self._extract_components(text)
            person_name = extracted.get("person_name", "")
            phone = extracted.get("phone", "")
            address_text = extracted.get("address", "")
            
            if not address_text:
                # 如果没有地址信息，返回原文本
                return {
                    "original_text": text,
                    "corrected_text": text,
                    "address_info": {},
                    "message": "未检测到地址信息"
                }
            
            # 步骤2: 对地址部分进行纠错
            corrected_address = self._correct_text(address_text)
            
            # 步骤3: 补全地址信息
            address_info = self._complete_address(corrected_address)
            
            # 步骤4: 重新组合：处理后的地址 + 人名 + 电话
            # 保持原格式：地址部分保持原样（可能没有空格），人名和电话用空格分隔
            parts = []
            if corrected_address:
                parts.append(corrected_address)
            if person_name:
                parts.append(person_name)
            if phone:
                parts.append(phone)
            
            # 用空格连接各部分（地址、人名、电话之间用空格分隔）
            corrected_text = " ".join(parts)
            
            return {
                "original_text": text,
                "corrected_text": corrected_text,
                "address_info": address_info
            }
            
        except Exception as e:
            error_msg = f"预处理失败: {str(e)}"
            logger.error(f"预处理错误: {error_msg}", exc_info=True)
            return {
                "original_text": text,
                "corrected_text": text,
                "address_info": {},
                "error": error_msg
            }
    
    def _extract_components(self, text: str) -> Dict[str, str]:
        """
        从文本中提取人名、电话和地址信息
        
        Args:
            text: 输入文本，格式：地址信息 人名 电话
            示例：广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575
            
        Returns:
            包含person_name, phone, address的字典
        """
        result = {
            "person_name": "",
            "phone": "",
            "address": ""
        }
        
        original_text = text
        
        # 步骤1: 提取电话号码（11位手机号）
        phone_match = re.search(PHONE_PATTERN, text)
        if phone_match:
            result["phone"] = phone_match.group(0)
            phone_start = phone_match.start()
            phone_end = phone_match.end()
            # 移除电话（保留前后文本用于定位）
            text_before_phone = text[:phone_start]
            text_after_phone = text[phone_end:]
        else:
            # 尝试提取固定电话（带区号）
            fixed_phone_match = re.search(FIXED_PHONE_PATTERN, text)
            if fixed_phone_match:
                result["phone"] = fixed_phone_match.group(0)
                phone_start = fixed_phone_match.start()
                phone_end = fixed_phone_match.end()
                text_before_phone = text[:phone_start]
                text_after_phone = text[phone_end:]
            else:
                text_before_phone = text
                text_after_phone = ""
        
        # 步骤2: 从电话前面的文本中提取人名和地址
        remaining_text = text_before_phone.strip()
        
        if not remaining_text:
            return result
        
        # 按空格分割（地址可能是连续的，但人名通常在最后，用空格分隔）
        parts = remaining_text.split()
        
        if not parts:
            # 如果没有空格，整个文本可能是地址
            result["address"] = remaining_text
            return result
        
        # 尝试识别地址关键词（使用常量）
        
        # 策略：从前往后找地址部分，从后往前找人名部分
        address_parts = []
        person_parts = []
        
        # 找到第一个包含地址关键词的部分
        address_start_idx = -1
        for i, part in enumerate(parts):
            if any(keyword in part for keyword in ADDRESS_KEYWORDS) or bool(re.search(r'\d', part)):
                address_start_idx = i
                break
        
        if address_start_idx >= 0:
            # 从地址开始位置往前收集所有地址部分
            i = address_start_idx
            while i < len(parts):
                part = parts[i]
                part_has_address_keyword = any(keyword in part for keyword in ADDRESS_KEYWORDS)
                has_number = bool(re.search(r'\d', part))
                is_person = re.match(CHINESE_NAME_PATTERN, part) and not part_has_address_keyword
                
                if is_person:
                    # 遇到可能是人名的部分，停止地址收集
                    person_parts.append(part)
                    # 后续部分都可能是人名
                    if i + 1 < len(parts):
                        person_parts.extend(parts[i + 1:])
                    break
                elif part_has_address_keyword or has_number:
                    # 是地址的一部分
                    address_parts.append(part)
                else:
                    # 不确定，如果前面已经有地址部分，则归为地址
                    if address_parts:
                        address_parts.append(part)
                    else:
                        person_parts.append(part)
                i += 1
            
            # 处理地址开始位置之前的部分
            if address_start_idx > 0:
                # 前面的部分可能是地址的一部分（如果地址没有空格）
                # 或者可能是人名
                for i in range(address_start_idx):
                    part = parts[i]
                    is_person = re.match(CHINESE_NAME_PATTERN, part)
                    if is_person:
                        person_parts.insert(0, part)
                    else:
                        # 可能是地址的一部分（地址可能没有空格被分割）
                        address_parts.insert(0, part)
        else:
            # 没有找到明确的地址关键词，尝试其他方法
            # 如果包含数字，可能是地址
            for part in parts:
                has_number = bool(re.search(r'\d', part))
                is_person = re.match(CHINESE_NAME_PATTERN, part)
                
                if has_number and len(part) > 2:
                    address_parts.append(part)
                elif is_person:
                    person_parts.append(part)
                else:
                    # 不确定，优先归为地址
                    address_parts.append(part)
        
        # 组合地址部分
        if address_parts:
            # 检查原文本中地址部分是否连续（没有空格）
            # 如果原文本中这些部分之间没有空格，则组合时也不加空格
            address_text = ""
            for i, part in enumerate(address_parts):
                if i == 0:
                    address_text = part
                else:
                    # 检查原文本中这两个部分之间是否有空格
                    prev_part = address_parts[i-1]
                    # 在原始文本中查找这两个部分
                    pattern = re.escape(prev_part) + r'\s+' + re.escape(part)
                    if re.search(pattern, original_text):
                        address_text += " " + part
                    else:
                        # 没有空格，直接连接
                        address_text += part
            result["address"] = address_text
        
        # 组合人名部分
        if person_parts:
            result["person_name"] = " ".join(person_parts)
        
        return result
    
    def _correct_text(self, text: str) -> str:
        """
        使用大模型进行文本纠错
        
        Args:
            text: 待纠错的文本
            
        Returns:
            纠错后的文本
        """
        try:
            prompt = f"""请对以下文本进行错字纠错，只纠正错别字，不要改变文本的意思和结构。只返回纠错后的文本，不要添加任何解释。

原文：
{text}

纠错后的文本："""
            
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                max_tokens=500,
                temperature=0.1,
                api_key=self.api_key
            )
            
            if response.status_code == 200:
                corrected = response.output.text.strip()
                return corrected
            else:
                logger.warning(f"纠错失败: {response.message}")
                return text
                
        except Exception as e:
            logger.error(f"文本纠错出错: {str(e)}", exc_info=True)
            return text
    
    def _complete_address(self, address_text: str) -> Dict[str, Any]:
        """
        使用大模型补全地址信息
        
        Args:
            address_text: 地址文本
            
        Returns:
            补全的地址信息字典，包含：
            - ProvinceName: 省份
            - CityName: 城市
            - ExpAreaName: 所在地区/县级市
            - StreetName: 街道名称
            - Address: 详细地址
        """
        try:
            prompt = f"""请从以下文本中提取并补全地址信息，按照JSON格式返回。只处理地址相关信息，忽略人名和电话。

要求：
1. 只提取地址相关信息，忽略人名和电话
2. 按照以下字段格式返回（所有字段都是字符串类型）：
   - ProvinceName: 省份（如：浙江省），如果无法提取则返回空字符串
   - CityName: 城市（如：杭州市），如果无法提取则返回空字符串
   - ExpAreaName: 所在地区/县级市（如：余杭区），如果无法提取则返回空字符串
   - StreetName: 街道名称（如：文一西路），如果无法提取则返回空字符串
   - Address: 详细地址（如：969号或具体门牌号），如果无法提取则返回空字符串

3. 返回格式必须是有效的JSON对象，只包含这5个字段，不要添加其他字段
4. 如果地址信息不完整，请根据上下文合理推断补全，但不要编造不存在的信息
5. 字段值不要包含引号外的其他字符

文本内容：
{address_text}

请只返回JSON格式，不要添加任何解释："""
            
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                max_tokens=500,
                temperature=0.1,
                api_key=self.api_key
            )
            
            if response.status_code == 200:
                result_text = response.output.text.strip()
                
                # 尝试提取JSON（支持多行JSON）
                # 先尝试直接解析
                try:
                    address_info = json.loads(result_text)
                except json.JSONDecodeError:
                    # 如果直接解析失败，尝试提取JSON对象
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            address_info = json.loads(json_str)
                        except json.JSONDecodeError:
                            logger.warning(f"JSON解析失败: {json_str}")
                            return self._default_address_info()
                    else:
                        logger.warning(f"未找到JSON格式: {result_text}")
                        return self._default_address_info()
                
                # 确保所有字段都存在，并转换为字符串
                result = {
                    "ProvinceName": str(address_info.get("ProvinceName", "")).strip(),
                    "CityName": str(address_info.get("CityName", "")).strip(),
                    "ExpAreaName": str(address_info.get("ExpAreaName", "")).strip(),
                    "StreetName": str(address_info.get("StreetName", "")).strip(),
                    "Address": str(address_info.get("Address", "")).strip()
                }
                
                return result
            else:
                logger.warning(f"地址补全失败: {response.message}")
                return self._default_address_info()
                
        except Exception as e:
            logger.error(f"地址补全出错: {str(e)}", exc_info=True)
            return self._default_address_info()
    
    def _default_address_info(self) -> Dict[str, str]:
        """返回默认的空地址信息"""
        return {
            "ProvinceName": "",
            "CityName": "",
            "ExpAreaName": "",
            "StreetName": "",
            "Address": ""
        }


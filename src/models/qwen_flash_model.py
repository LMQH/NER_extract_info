"""
Qwen-Flash模型调用模块
使用DashScope的qwen-flash大模型进行地址纠错、补全和实体提取
一次性完成纠错、补全和实体提取，返回统一格式
"""
import os
import json
import re
from typing import Dict, Any, Optional
from dashscope import Generation
from src.processor_mgeo.converters import reorder_data_fields
from ..utils.logger import get_logger

logger = get_logger(__name__)


class QwenFlashModel:
    """Qwen-Flash模型封装类，用于地址纠错、补全和实体提取"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Qwen-Flash模型
        
        Args:
            api_key: DashScope API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("未找到DASHSCOPE_API_KEY，请在环境配置文件中设置")
        
        # 设置API密钥
        os.environ['DASHSCOPE_API_KEY'] = self.api_key
        
        self.model_name = 'qwen-flash'
        self.ebusiness_id = "2223333"
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        从文本中抽取实体（一次性完成纠错、补全和实体提取）
        
        Args:
            text: 输入文本，格式：地址信息 人名 电话
            
        Returns:
            抽取结果字典，包含:
            - EBusinessID: 业务ID
            - Data: 提取的实体数据
            - Success: 是否成功
            - Reason: 原因说明
            - ResultCode: 结果代码
        """
        if not text or not text.strip():
            data = {
                "ProvinceName": "",
                "CityName": "",
                "ExpAreaName": "",
                "StreetName": "",
                "Address": "",
                "Mobile": "",
                "Name": ""
            }
            return {
                "EBusinessID": self.ebusiness_id,
                "Data": reorder_data_fields(data),
                "Success": False,
                "Reason": "输入文本为空",
                "ResultCode": "101"  # 101: 接口请求参数错误
            }
        
        try:
            # 步骤1: 提取人名、电话和地址
            extracted = self._extract_components(text)
            person_name = extracted.get("person_name", "")
            phone = extracted.get("phone", "")
            address_text = extracted.get("address", "")
            
            if not address_text:
                data = {
                    "ProvinceName": "",
                    "CityName": "",
                    "ExpAreaName": "",
                    "StreetName": "",
                    "Address": "",
                    "Mobile": phone,
                    "Name": person_name
                }
                return {
                    "EBusinessID": self.ebusiness_id,
                    "Data": reorder_data_fields(data),
                    "Success": False,
                    "Reason": "未检测到地址信息",
                    "ResultCode": "102"  # 102: 地理模型解析失败（地址信息无法解析）
                }
            
            # 步骤2: 对地址部分进行纠错
            corrected_address = self._correct_text(address_text)
            
            # 步骤3: 补全地址信息并提取实体
            address_info = self._complete_address_and_extract_entities(corrected_address)
            
            # 步骤4: 构建返回结果
            data = {
                "ProvinceName": address_info.get("ProvinceName", ""),
                "CityName": address_info.get("CityName", ""),
                "ExpAreaName": address_info.get("ExpAreaName", ""),
                "StreetName": address_info.get("StreetName", ""),
                "Address": address_info.get("Address", ""),
                "Mobile": phone,
                "Name": person_name
            }
            result = {
                "EBusinessID": self.ebusiness_id,
                "Data": reorder_data_fields(data),
                "Success": True,
                "Reason": "解析成功",
                "ResultCode": "100"
            }
            
            return result
            
        except Exception as e:
            error_msg = f"实体提取失败: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.debug(traceback.format_exc())
            data = {
                "ProvinceName": "",
                "CityName": "",
                "ExpAreaName": "",
                "StreetName": "",
                "Address": "",
                "Mobile": "",
                "Name": ""
            }
            return {
                "EBusinessID": self.ebusiness_id,
                "Data": reorder_data_fields(data),
                "Success": False,
                "Reason": error_msg,
                "ResultCode": "102"  # 102: 地理模型解析失败（模型处理失败）
            }
    
    def _extract_components(self, text: str) -> Dict[str, str]:
        """
        从文本中提取人名、电话和地址信息
        
        Args:
            text: 输入文本，格式：地址信息 人名 电话
            
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
        phone_pattern = r'1[3-9]\d{9}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            result["phone"] = phone_match.group(0)
            phone_start = phone_match.start()
            phone_end = phone_match.end()
            text_before_phone = text[:phone_start]
            text_after_phone = text[phone_end:]
        else:
            # 尝试提取固定电话（带区号）
            fixed_phone_pattern = r'0\d{2,3}-?\d{7,8}'
            fixed_phone_match = re.search(fixed_phone_pattern, text)
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
        
        # 按空格分割
        parts = remaining_text.split()
        
        if not parts:
            result["address"] = remaining_text
            return result
        
        # 尝试识别地址关键词
        address_keywords = ['省', '市', '区', '县', '镇', '街道', '路', '街', '号', '村', '组', 
                           '小区', '大厦', '广场', '园区', '工业区', '开发区', '新区', '大道', 
                           '巷', '弄', '里', '幢', '栋', '单元', '室', '层']
        
        # 策略：从前往后找地址部分，从后往前找人名部分
        address_parts = []
        person_parts = []
        
        # 找到第一个包含地址关键词的部分
        address_start_idx = -1
        for i, part in enumerate(parts):
            if any(keyword in part for keyword in address_keywords) or bool(re.search(r'\d', part)):
                address_start_idx = i
                break
        
        if address_start_idx >= 0:
            # 从地址开始位置往前收集所有地址部分
            i = address_start_idx
            while i < len(parts):
                part = parts[i]
                part_has_address_keyword = any(keyword in part for keyword in address_keywords)
                has_number = bool(re.search(r'\d', part))
                is_person = re.match(r'^[\u4e00-\u9fa5]{2,4}$', part) and not part_has_address_keyword
                
                if is_person:
                    person_parts.append(part)
                    if i + 1 < len(parts):
                        person_parts.extend(parts[i + 1:])
                    break
                elif part_has_address_keyword or has_number:
                    address_parts.append(part)
                else:
                    if address_parts:
                        address_parts.append(part)
                    else:
                        person_parts.append(part)
                i += 1
            
            # 处理地址开始位置之前的部分
            if address_start_idx > 0:
                for i in range(address_start_idx):
                    part = parts[i]
                    is_person = re.match(r'^[\u4e00-\u9fa5]{2,4}$', part)
                    if is_person:
                        person_parts.insert(0, part)
                    else:
                        address_parts.insert(0, part)
        else:
            # 没有找到明确的地址关键词，尝试其他方法
            for part in parts:
                has_number = bool(re.search(r'\d', part))
                is_person = re.match(r'^[\u4e00-\u9fa5]{2,4}$', part)
                
                if has_number and len(part) > 2:
                    address_parts.append(part)
                elif is_person:
                    person_parts.append(part)
                else:
                    address_parts.append(part)
        
        # 组合地址部分
        if address_parts:
            address_text = ""
            for i, part in enumerate(address_parts):
                if i == 0:
                    address_text = part
                else:
                    prev_part = address_parts[i-1]
                    pattern = re.escape(prev_part) + r'\s+' + re.escape(part)
                    if re.search(pattern, original_text):
                        address_text += " " + part
                    else:
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
            logger.error(f"文本纠错出错: {str(e)}")
            return text
    
    def _complete_address_and_extract_entities(self, address_text: str) -> Dict[str, Any]:
        """
        使用大模型补全地址信息并提取实体
        
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
   - ProvinceName: 省份（如：广东省），如果无法提取则返回空字符串
   - CityName: 城市（如：深圳市），如果无法提取则返回空字符串
   - ExpAreaName: 所在地区/县级市（如：龙岗区），如果无法提取则返回空字符串
   - StreetName: 街道名称（如：坂田街道），如果无法提取则返回空字符串
   - Address: 详细地址（如：长坑路西2巷2号202或具体门牌号），如果无法提取则返回空字符串

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
                
                # 尝试提取JSON
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
            logger.error(f"地址补全出错: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
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


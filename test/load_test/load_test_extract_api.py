#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实体抽取API压测脚本
重点测试并发性能和响应时间

使用方法:
    方式1: 使用配置文件（推荐）
        python test/load_test/load_test_extract_api.py
        # 配置文件: test/load_test/load_test_config.json
    
    方式2: 命令行参数
        python test/load_test/load_test_extract_api.py --url http://localhost:13110/ner_extract_info/api/extract --concurrent 10 --total 100
    
    方式3: 混合使用（命令行参数会覆盖配置文件）
        python test/load_test/load_test_extract_api.py --concurrent 20
"""

import asyncio
import aiohttp
import time
import argparse
import json
import statistics
import os
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime


class LoadTestResult:
    """压测结果统计"""
    
    def __init__(self, t1: float = 1.0, t2: float = 3.0):
        self.response_times: List[float] = []
        self.fast_count = 0  # 快速请求（响应时间 < T1）
        self.slow_count = 0  # 慢请求（T1 ≤ 响应时间 ≤ T2）
        self.bad_count = 0   # 坏请求（响应时间 > T2 或超时/失败）
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.errors: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.t1 = t1  # 快速阈值（默认1秒）
        self.t2 = t2  # 慢速阈值（默认3秒）
        
    def add_result(self, response_time: float, status_code: int, error: Optional[str] = None):
        """添加一次请求结果"""
        self.response_times.append(response_time)
        
        # 三档统计逻辑
        if status_code == 200:
            # HTTP 200 成功请求，根据响应时间分类
            if response_time < self.t1:
                self.fast_count += 1  # fast: < T1
            elif response_time <= self.t2:
                self.slow_count += 1  # slow: T1 ~ T2
            else:
                self.bad_count += 1  # bad: > T2
        else:
            # HTTP 非200 或超时，视为 bad
            self.bad_count += 1
            if error:
                self.errors.append(error)
        
        self.status_codes[status_code] += 1
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        total_requests = len(self.response_times)
        
        stats = {
            'total_requests': total_requests,
            'fast_count': self.fast_count,  # 快速请求数
            'slow_count': self.slow_count,   # 慢请求数
            'bad_count': self.bad_count,    # 坏请求数
            'fast_rate': (self.fast_count / total_requests * 100) if total_requests > 0 else 0,  # 快速请求率
            'slow_rate': (self.slow_count / total_requests * 100) if total_requests > 0 else 0,  # 慢请求率
            'bad_rate': (self.bad_count / total_requests * 100) if total_requests > 0 else 0,   # 坏请求率
            'status_codes': dict(self.status_codes),
            'response_time': {
                'min': min(self.response_times),
                'max': max(self.response_times),
                'mean': statistics.mean(self.response_times),
                'median': statistics.median(self.response_times),
            },
            't1': self.t1,  # 快速阈值
            't2': self.t2   # 慢速阈值
        }
        
        # 计算百分位数
        if total_requests > 0:
            stats['response_time']['p50'] = sorted_times[int(total_requests * 0.50)]
            stats['response_time']['p90'] = sorted_times[int(total_requests * 0.90)]
            stats['response_time']['p95'] = sorted_times[int(total_requests * 0.95)]
            stats['response_time']['p99'] = sorted_times[int(total_requests * 0.99)]
        
        # 计算QPS
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            stats['duration'] = duration
            stats['qps'] = total_requests / duration if duration > 0 else 0
        
        return stats
    
    def generate_report_text(self, test_config: Optional[Dict] = None) -> str:
        """生成测试报告文本"""
        stats = self.get_statistics()
        lines = []
        
        lines.append("="*80)
        lines.append("压测报告")
        lines.append("="*80)
        lines.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if test_config:
            lines.append(f"\n【测试配置】")
            for key, value in test_config.items():
                lines.append(f"  {key}: {value}")
        
        lines.append(f"\n【请求统计】（三档分类）")
        t1 = stats.get('t1', 1.0)
        t2 = stats.get('t2', 3.0)
        lines.append(f"  总请求数: {stats['total_requests']}")
        lines.append(f"  快速请求 (fast): {stats['fast_count']} (响应时间 < {t1:.1f}秒) - {stats['fast_rate']:.2f}%")
        lines.append(f"  慢速请求 (slow): {stats['slow_count']} ({t1:.1f}秒 ≤ 响应时间 ≤ {t2:.1f}秒) - {stats['slow_rate']:.2f}%")
        lines.append(f"  坏请求 (bad): {stats['bad_count']} (响应时间 > {t2:.1f}秒 或超时/失败) - {stats['bad_rate']:.2f}%")
        
        if stats.get('duration'):
            lines.append(f"\n【性能统计】")
            lines.append(f"  测试时长: {stats['duration']:.2f} 秒")
            lines.append(f"  QPS: {stats['qps']:.2f}")
        
        lines.append(f"\n【响应时间统计】(单位: 秒)")
        rt = stats['response_time']
        lines.append(f"  最小值: {rt['min']:.3f}s")
        lines.append(f"  最大值: {rt['max']:.3f}s")
        lines.append(f"  平均值: {rt['mean']:.3f}s")
        lines.append(f"  中位数: {rt['median']:.3f}s")
        if 'p50' in rt:
            lines.append(f"  P50: {rt['p50']:.3f}s")
            lines.append(f"  P90: {rt['p90']:.3f}s")
            lines.append(f"  P95: {rt['p95']:.3f}s")
            lines.append(f"  P99: {rt['p99']:.3f}s")
        
        lines.append(f"\n【HTTP状态码统计】")
        for code, count in sorted(stats['status_codes'].items()):
            lines.append(f"  {code}: {count}")
        
        if self.errors:
            lines.append(f"\n【错误信息】(前50条)")
            for error in self.errors[:50]:
                lines.append(f"  {error}")
            if len(self.errors) > 50:
                lines.append(f"  ... 还有 {len(self.errors) - 50} 条错误")
        
        lines.append("="*80)
        
        return "\n".join(lines)
    
    def save_report(self, report_text: str, output_dir: str = "test/load_test/reports", test_config: Optional[Dict] = None) -> str:
        """保存报告到文件，返回文件路径"""
        # 创建报告目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 根据测试模式生成文件名前缀
        mode_prefix = ""
        if test_config:
            if test_config.get('total_requests'):
                mode_prefix = "total"
            elif test_config.get('duration'):
                mode_prefix = "duration"
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if mode_prefix:
            filename = f"load_test_report_{mode_prefix}_{timestamp}.txt"
        else:
            filename = f"load_test_report_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # 保存报告
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return filepath
    
    def save_report_json(self, test_config: Optional[Dict] = None, output_dir: str = "test/load_test/reports") -> str:
        """保存JSON格式的报告，返回文件路径"""
        # 创建报告目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 根据测试模式生成文件名前缀
        mode_prefix = ""
        if test_config:
            if test_config.get('total_requests'):
                mode_prefix = "total"
            elif test_config.get('duration'):
                mode_prefix = "duration"
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if mode_prefix:
            filename = f"load_test_report_{mode_prefix}_{timestamp}.json"
        else:
            filename = f"load_test_report_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # 准备JSON数据
        stats = self.get_statistics()
        report_data = {
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_config': test_config or {},
            'statistics': stats,
            'errors': self.errors[:100] if self.errors else []  # 只保存前100条错误
        }
        
        # 保存JSON报告
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return filepath


async def make_request(
    session: aiohttp.ClientSession,
    url: str,
    payload: Dict,
    timeout: int = 5
) -> Tuple[float, int, Optional[str]]:
    """发送单个请求"""
    start_time = time.time()
    status_code = 0
    error = None
    
    try:
        async with session.post(
            url,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            status_code = response.status
            response_time = time.time() - start_time
            
            # 尝试读取响应内容（用于验证）
            try:
                await response.json()
            except:
                await response.text()
            
            return response_time, status_code, None
            
    except asyncio.TimeoutError:
        response_time = time.time() - start_time
        error = f"请求超时 (>{timeout}s)"
        return response_time, 0, error
        
    except aiohttp.ClientError as e:
        response_time = time.time() - start_time
        error = f"客户端错误: {str(e)}"
        return response_time, 0, error
        
    except Exception as e:
        response_time = time.time() - start_time
        error = f"未知错误: {str(e)}"
        return response_time, 0, error


async def worker(
    session: aiohttp.ClientSession,
    url: str,
    payload: Dict,
    result: LoadTestResult,
    semaphore: asyncio.Semaphore,
    total_requests: Optional[int] = None,
    timeout: int = 5
):
    """工作协程：持续发送请求"""
    while True:
        # 检查是否达到总请求数（在获取信号量之前检查，避免不必要的等待）
        if total_requests is not None:
            current_total = result.fast_count + result.slow_count + result.bad_count
            if current_total >= total_requests:
                break
        
        async with semaphore:
            # 再次检查（因为可能有并发竞争）
            if total_requests is not None:
                current_total = result.fast_count + result.slow_count + result.bad_count
                if current_total >= total_requests:
                    break
            
            response_time, status_code, error = await make_request(session, url, payload, timeout)
            result.add_result(response_time, status_code, error)


async def run_load_test(
    url: str,
    concurrent: int,
    total: Optional[int] = None,
    duration: Optional[int] = None,
    payload: Optional[Dict] = None,
    timeout: int = 5,
    t1: float = 1.0,
    t2: float = 3.0
):
    """运行压测"""
    if payload is None:
        payload = {
            "Content": "广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575"
        }
    
    # 使用 T1 和 T2 作为三档统计阈值
    result = LoadTestResult(t1=t1, t2=t2)
    result.start_time = time.time()
    
    # 创建信号量控制并发数
    semaphore = asyncio.Semaphore(concurrent)
    
    # 创建HTTP会话
    connector = aiohttp.TCPConnector(limit=concurrent * 2, limit_per_host=concurrent * 2)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 创建worker任务
        tasks = []
        
        for _ in range(concurrent):
            task = asyncio.create_task(
                worker(session, url, payload, result, semaphore, total, timeout)
            )
            tasks.append(task)
        
        # 如果设置了持续时间，在指定时间后停止
        if duration:
            await asyncio.sleep(duration)
            # 取消所有任务
            for task in tasks:
                task.cancel()
            # 等待任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 等待所有任务完成
            await asyncio.gather(*tasks)
    
    result.end_time = time.time()
    return result


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"警告: 无法读取配置文件 {config_path}: {str(e)}")
        return {}


def normalize_to_list(value):
    """将值转换为列表，如果不是列表则包装为单元素列表"""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    return [value]


def detect_batch_mode(config: Dict) -> Tuple[bool, Optional[str], List]:
    """
    检测是否启用批量测试模式
    返回: (是否批量模式, 批量参数名, 参数值列表)
    """
    # 检查concurrent是否为数组
    if 'concurrent' in config and isinstance(config['concurrent'], list) and len(config['concurrent']) > 1:
        return True, 'concurrent', config['concurrent']
    
    # 检查total是否为数组
    if 'total' in config and isinstance(config['total'], list) and len(config['total']) > 1:
        return True, 'total', config['total']
    
    # 检查duration是否为数组
    if 'duration' in config and isinstance(config['duration'], list) and len(config['duration']) > 1:
        return True, 'duration', config['duration']
    
    return False, None, []


def generate_summary_report(batch_results: List[Dict], batch_param: str, base_config: Dict, output_dir: str) -> str:
    """生成批量测试汇总报告"""
    lines = []
    
    lines.append("="*80)
    lines.append("批量压测汇总报告")
    lines.append("="*80)
    lines.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    lines.append(f"\n【测试配置】")
    lines.append(f"  URL: {base_config.get('url', 'N/A')}")
    lines.append(f"  批量参数: {batch_param}")
    lines.append(f"  测试参数值: {[r['param_value'] for r in batch_results]}")
    
    # 固定参数
    fixed_params = []
    if base_config.get('total') and not isinstance(base_config.get('total'), list):
        fixed_params.append(f"total={base_config['total']}")
    if base_config.get('duration') and not isinstance(base_config.get('duration'), list):
        fixed_params.append(f"duration={base_config['duration']}秒")
    if base_config.get('timeout'):
        fixed_params.append(f"timeout={base_config['timeout']}秒")
    if fixed_params:
        lines.append(f"  固定参数: {', '.join(fixed_params)}")
    
    # 获取T1和T2阈值（从第一个结果中获取）
    t1 = batch_results[0]['result'].t1 if batch_results else 1.0
    t2 = batch_results[0]['result'].t2 if batch_results else 3.0
    
    lines.append(f"\n【性能对比表】（三档分类: fast<{t1:.1f}s, slow {t1:.1f}s~{t2:.1f}s, bad>{t2:.1f}s）")
    # 表头
    header = f"{batch_param:>12} | {'总请求':>8} | {'Fast':>6} | {'Slow':>6} | {'Bad':>6} | {'Fast率':>8} | {'Slow率':>8} | {'Bad率':>8} | {'QPS':>10} | {'平均响应时间':>14} | {'P95响应时间':>14}"
    lines.append(header)
    lines.append("-" * len(header))
    
    # 数据行
    for result in batch_results:
        stats = result['result'].get_statistics()
        param_val = result['param_value']
        total_req = stats.get('total_requests', 0)
        fast = stats.get('fast_count', 0)
        slow = stats.get('slow_count', 0)
        bad = stats.get('bad_count', 0)
        fast_rate = stats.get('fast_rate', 0)
        slow_rate = stats.get('slow_rate', 0)
        bad_rate = stats.get('bad_rate', 0)
        qps = stats.get('qps', 0)
        avg_rt = stats.get('response_time', {}).get('mean', 0)
        p95_rt = stats.get('response_time', {}).get('p95', 0)
        
        row = f"{param_val:>12} | {total_req:>8} | {fast:>6} | {slow:>6} | {bad:>6} | {fast_rate:>7.2f}% | {slow_rate:>7.2f}% | {bad_rate:>7.2f}% | {qps:>10.2f} | {avg_rt:>13.3f}s | {p95_rt:>13.3f}s"
        lines.append(row)
    
    # 性能趋势分析
    lines.append(f"\n【性能趋势分析】")
    
    # 找出QPS峰值
    max_qps_result = max(batch_results, key=lambda r: r['result'].get_statistics().get('qps', 0))
    max_qps = max_qps_result['result'].get_statistics().get('qps', 0)
    max_qps_param = max_qps_result['param_value']
    lines.append(f"- QPS峰值: {max_qps:.2f} ({batch_param}={max_qps_param})")
    
    # 找出最优配置（Fast率>80%且QPS较高）
    best_results = [r for r in batch_results if r['result'].get_statistics().get('fast_rate', 0) >= 80]
    if best_results:
        best_result = max(best_results, key=lambda r: r['result'].get_statistics().get('qps', 0))
        best_qps = best_result['result'].get_statistics().get('qps', 0)
        best_fast_rate = best_result['result'].get_statistics().get('fast_rate', 0)
        best_bad_rate = best_result['result'].get_statistics().get('bad_rate', 0)
        best_param = best_result['param_value']
        lines.append(f"- 推荐配置: {batch_param}={best_param} (QPS={best_qps:.2f}, Fast率={best_fast_rate:.2f}%, Bad率={best_bad_rate:.2f}%)")
    
    # 响应时间趋势
    rt_values = [r['result'].get_statistics().get('response_time', {}).get('mean', 0) for r in batch_results]
    if len(rt_values) > 1:
        rt_increase = rt_values[-1] - rt_values[0]
        if rt_increase > 0.1:
            lines.append(f"- 响应时间变化: 从 {rt_values[0]:.3f}s 增加到 {rt_values[-1]:.3f}s (增加 {rt_increase:.3f}s)")
            # 找出响应时间明显上升的点
            for i in range(1, len(rt_values)):
                if rt_values[i] - rt_values[i-1] > rt_values[0] * 0.3:  # 增加超过30%
                    lines.append(f"- 响应时间拐点: {batch_param}={batch_results[i-1]['param_value']} -> {batch_results[i]['param_value']}")
                    break
    
    # 详细报告链接
    lines.append(f"\n【详细报告】")
    lines.append("每个测试的详细报告已单独保存:")
    for i, result in enumerate(batch_results, 1):
        report_file = result.get('report_file', 'N/A')
        lines.append(f"  {i}. {batch_param}={result['param_value']}: {os.path.basename(report_file)}")
    
    lines.append("="*80)
    
    return "\n".join(lines)


def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(script_dir, 'load_test_config.json')
    
    parser = argparse.ArgumentParser(
        description='实体抽取API压测脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用配置文件（推荐）
  python test/load_test/load_test_extract_api.py
  
  # 命令行参数覆盖配置文件
  python test/load_test/load_test_extract_api.py --concurrent 20 --total 200
  
  # 完全使用命令行参数
  python test/load_test/load_test_extract_api.py --url http://localhost:13110/ner_extract_info/api/extract --concurrent 10 --total 100
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=default_config_path,
        help=f'配置文件路径 (默认: {default_config_path})'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default=None,
        help='API接口地址 (例如: http://localhost:13110/ner_extract_info/api/extract)'
    )
    
    parser.add_argument(
        '--concurrent',
        type=int,
        default=None,
        help='并发数'
    )
    
    parser.add_argument(
        '--total',
        type=int,
        default=None,
        help='总请求数'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='测试持续时间(秒)'
    )
    
    parser.add_argument(
        '--content',
        type=str,
        default=None,
        help='请求内容'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=None,
        help='请求超时时间(秒)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='报告保存目录'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='同时保存JSON格式的报告'
    )
    
    args = parser.parse_args()
    
    # 加载配置文件
    config = load_config(args.config)
    
    # 合并配置：配置文件 -> 默认值 -> 命令行参数（优先级最高）
    url = args.url or config.get('url') or None
    
    # 检测批量测试模式（仅在配置文件模式下，命令行参数不支持批量）
    is_batch_mode = False
    batch_param = None
    batch_values = []
    
    if args.concurrent is None and args.total is None and args.duration is None:
        # 只有在没有命令行参数覆盖时才检测批量模式
        is_batch_mode, batch_param, batch_values = detect_batch_mode(config)
    
    # 根据是否批量模式处理参数
    if is_batch_mode:
        # 批量模式下，批量参数保持为数组，其他参数取第一个值或默认值
        if batch_param == 'concurrent':
            concurrent = config.get('concurrent', [10])  # 保持数组
        else:
            concurrent_val = config.get('concurrent', 10)
            concurrent = concurrent_val if not isinstance(concurrent_val, list) else concurrent_val[0] if concurrent_val else 10
        
        if batch_param == 'total':
            total = config.get('total')  # 保持数组或None
        else:
            total_val = config.get('total')
            total = total_val if not isinstance(total_val, list) else None
        
        if batch_param == 'duration':
            duration = config.get('duration')  # 保持数组或None
        else:
            duration_val = config.get('duration')
            duration = duration_val if not isinstance(duration_val, list) else None
    else:
        # 非批量模式，正常处理
        concurrent = args.concurrent if args.concurrent is not None else config.get('concurrent', 10)
        total = args.total if args.total is not None else config.get('total')
        duration = args.duration if args.duration is not None else config.get('duration')
    
    content = args.content or config.get('content') or "广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575"
    timeout = args.timeout if args.timeout is not None else config.get('timeout', 5)
    output_dir = args.output_dir or config.get('output_dir') or 'test/load_test/reports'
    # json参数：如果命令行提供了--json则为True，否则使用配置文件中的值，都没有则False
    json_report = args.json if args.json else config.get('json', False)
    # T1和T2阈值配置（三档统计）
    t1 = config.get('t1', 1.0)  # 快速阈值，默认1秒
    t2 = config.get('t2', 3.0)  # 慢速阈值，默认3秒
    
    # 验证必需参数
    if not url:
        parser.error("必须提供 --url 参数或在配置文件中设置 url")
    
    # 批量模式下，验证逻辑不同
    if not is_batch_mode:
        if total is None and duration is None:
            parser.error("必须提供 --total 或 --duration 参数，或在配置文件中设置其中一个")
        
        if total is not None and duration is not None:
            parser.error("--total 和 --duration 不能同时设置")
    
    # 准备请求负载
    payload = {
        "Content": content
    }
    
    # 批量测试模式
    if is_batch_mode:
        print(f"\n{'='*80}")
        print(f"批量压测模式")
        print(f"{'='*80}")
        print(f"批量参数: {batch_param}")
        print(f"参数值列表: {batch_values}")
        print(f"目标URL: {url}")
        print(f"超时设置: {timeout}秒")
        print(f"请求内容: {payload['Content']}")
        
        # 获取批量模式的配置
        batch_config = config.get('batch_mode', {})
        cooldown = batch_config.get('cooldown', 5)  # 每次测试之间的冷却时间（秒）
        
        batch_results = []
        total_tests = len(batch_values)
        
        try:
            for idx, param_value in enumerate(batch_values, 1):
                print(f"\n{'='*80}")
                print(f"测试 {idx}/{total_tests}: {batch_param} = {param_value}")
                print(f"{'='*80}")
                
                # 根据批量参数设置对应的值
                if batch_param == 'concurrent':
                    test_concurrent = param_value
                    test_total = total if not isinstance(total, list) else None
                    test_duration = duration if not isinstance(duration, list) else None
                elif batch_param == 'total':
                    test_concurrent = concurrent if not isinstance(concurrent, list) else (concurrent[0] if concurrent else 10)
                    test_total = param_value
                    test_duration = None
                elif batch_param == 'duration':
                    test_concurrent = concurrent if not isinstance(concurrent, list) else (concurrent[0] if concurrent else 10)
                    test_total = None
                    test_duration = param_value
                else:
                    # 不应该到这里
                    test_concurrent = 10
                    test_total = None
                    test_duration = None
                
                # 确保至少有一个测试条件（仅当批量参数不是total和duration时）
                if batch_param == 'concurrent':
                    if test_total is None and test_duration is None:
                        test_total = 500  # 默认值
                
                # 准备测试配置信息
                test_config = {
                    'url': url,
                    'concurrent': test_concurrent,
                    'total_requests': test_total,
                    'duration': test_duration,
                    'timeout': timeout,
                    'content': payload['Content'],
                    't1': t1,
                    't2': t2,
                    batch_param: param_value  # 记录批量参数值
                }
                
                # 运行单次测试
                result = asyncio.run(
                    run_load_test(
                        url=url,
                        concurrent=test_concurrent,
                        total=test_total,
                        duration=test_duration,
                        payload=payload,
                        timeout=timeout,
                        t1=t1,
                        t2=t2
                    )
                )
                
                # 生成并保存单次测试报告
                report_text = result.generate_report_text(test_config)
                report_file = result.save_report(report_text, output_dir, test_config)
                
                if json_report:
                    json_file = result.save_report_json(test_config, output_dir)
                
                print(f"✓ 测试完成: {batch_param}={param_value}")
                print(f"  - 报告: {os.path.basename(report_file)}")
                stats = result.get_statistics()
                print(f"  - QPS: {stats.get('qps', 0):.2f}")
                print(f"  - Fast: {stats.get('fast_count', 0)} ({stats.get('fast_rate', 0):.2f}%)")
                print(f"  - Slow: {stats.get('slow_count', 0)} ({stats.get('slow_rate', 0):.2f}%)")
                print(f"  - Bad: {stats.get('bad_count', 0)} ({stats.get('bad_rate', 0):.2f}%)")
                
                batch_results.append({
                    'param_value': param_value,
                    'result': result,
                    'report_file': report_file,
                    'test_config': test_config
                })
                
                # 测试间隔（最后一次不需要等待）
                if idx < total_tests:
                    print(f"\n等待 {cooldown} 秒后继续下一个测试...")
                    time.sleep(cooldown)
            
            # 生成汇总报告
            print(f"\n{'='*80}")
            print(f"生成汇总报告...")
            print(f"{'='*80}")
            
            base_config = {
                'url': url,
                'timeout': timeout,
                'content': payload['Content'],
                't1': t1,
                't2': t2
            }
            if batch_param != 'total' and total and not isinstance(total, list):
                base_config['total'] = total
            if batch_param != 'duration' and duration and not isinstance(duration, list):
                base_config['duration'] = duration
            
            summary_text = generate_summary_report(batch_results, batch_param, base_config, output_dir)
            
            # 保存汇总报告
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            summary_filename = f"load_test_summary_{batch_param}_{timestamp}.txt"
            summary_filepath = os.path.join(output_dir, summary_filename)
            
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                f.write(summary_text)
            
            print(f"\n✓ 汇总报告已保存: {summary_filepath}")
            print(f"\n批量测试完成！共完成 {total_tests} 个测试。")
            
        except KeyboardInterrupt:
            print("\n\n批量压测被用户中断")
            if batch_results:
                print(f"已完成 {len(batch_results)}/{total_tests} 个测试")
        except Exception as e:
            print(f"\n\n批量压测出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    else:
        # 单次测试模式（原有逻辑）
        print(f"\n开始压测...")
        if args.config and os.path.exists(args.config):
            print(f"  配置文件: {args.config}")
        print(f"  目标URL: {url}")
        print(f"  并发数: {concurrent}")
        if total:
            print(f"  总请求数: {total}")
        if duration:
            print(f"  持续时间: {duration}秒")
        print(f"  请求内容: {payload['Content']}")
        print(f"  超时设置: {timeout}秒")
        print()
        
        # 准备测试配置信息
        test_config = {
            'url': url,
            'concurrent': concurrent,
            'total_requests': total,
            'duration': duration,
            'timeout': timeout,
            'content': payload['Content'],
            't1': t1,
            't2': t2
        }
        
        # 运行压测
        try:
            result = asyncio.run(
                run_load_test(
                    url=url,
                    concurrent=concurrent,
                    total=total,
                    duration=duration,
                    payload=payload,
                    timeout=timeout,
                    t1=t1,
                    t2=t2
                )
            )
            
            # 生成报告文本
            report_text = result.generate_report_text(test_config)
            
            # 保存文本报告
            report_file = result.save_report(report_text, output_dir, test_config)
            print(f"\n✓ 测试报告已保存: {report_file}")
            
            # 如果指定了JSON格式，也保存JSON报告
            if json_report:
                json_file = result.save_report_json(test_config, output_dir)
                print(f"✓ JSON报告已保存: {json_file}")
            
        except KeyboardInterrupt:
            print("\n\n压测被用户中断")
        except Exception as e:
            print(f"\n\n压测出错: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()

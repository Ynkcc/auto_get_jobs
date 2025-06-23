#!/usr/bin/env python3
"""
测试main.py是否能够正常运行的脚本
"""
import subprocess
import time
import signal
import sys

def test_main_startup():
    """测试main.py是否能够正常启动"""
    print("正在测试main.py启动...")
    
    # 启动main.py进程
    process = subprocess.Popen(
        [sys.executable, "-m", "src.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    try:
        # 给程序10秒时间启动
        output_lines = []
        start_time = time.time()
        
        while time.time() - start_time < 10:
            if process.poll() is not None:
                # 进程已经结束
                break
                
            # 读取一行输出
            line = process.stderr.readline()
            if line:
                output_lines.append(line.strip())
                print(f"输出: {line.strip()}")
                
                # 检查关键的成功信息
                if "所有模块初始化完成" in line:
                    print("✅ 模块初始化成功")
                elif "事件订阅者注册完成" in line:
                    print("✅ 事件订阅者注册成功")
                elif "启动核心服务" in line:
                    print("✅ 核心服务启动成功")
                elif "请在浏览器中扫码登录" in line:
                    print("✅ 浏览器登录流程启动成功")
                    # 找到这个信息后就可以终止测试了
                    break
        
        # 终止进程
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)
        
        # 分析结果
        success_markers = [
            "所有模块初始化完成",
            "事件订阅者注册完成", 
            "启动核心服务"
        ]
        
        found_markers = 0
        for marker in success_markers:
            if any(marker in line for line in output_lines):
                found_markers += 1
        
        if found_markers == len(success_markers):
            print("🎉 测试成功！main.py能够正常启动和运行")
            return True
        else:
            print(f"❌ 测试失败！只找到了 {found_markers}/{len(success_markers)} 个成功标记")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()

if __name__ == "__main__":
    success = test_main_startup()
    sys.exit(0 if success else 1)

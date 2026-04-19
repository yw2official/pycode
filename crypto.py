import hashlib
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

def get_private_key_value():
    """
    第一步：计算私钥
    逻辑：SHA512("114514") -> 取前32字节 -> 转为整数
    """
    input_str = "114514"
    # 计算 SHA512
    digest = hashlib.sha512(input_str.encode('utf-8')).digest()
    # 取前 32 字节作为私钥 (P-256 私钥长度)
    private_key_bytes = digest[:32]
    private_key_int = int.from_bytes(private_key_bytes, byteorder='big')
    
    print(f"[*] 私钥 (前32字节 Hex): {private_key_bytes.hex()}")
    return private_key_int

def solve_puzzle():
    # 1. 获取私钥
    private_value = get_private_key_value()
    private_key = ec.derive_private_key(private_value, ec.SECP256R1(), default_backend())

    # 2. 从 crt.sh 获取 ip6.arpa 的证书列表
    print("[*] 正在查询 crt.sh 获取 ip6.arpa 证书列表 (可能需要几秒钟)...")
    url = "https://crt.sh/?q=ip6.arpa&output=json"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; CertChecker/1.0)'}
        response = requests.get(url, timeout=30, headers=headers)
        
        # 检查状态码
        if response.status_code != 200:
            print(f"[!] crt.sh 返回错误状态码: {response.status_code}")
            print(f"    响应内容: {response.text[:200]}...")
            return
        
        # 检查响应是否为空
        if not response.text.strip():
            print("[!] crt.sh 返回空响应，可能是服务繁忙，请稍后重试")
            return
        
        # 检查是否返回了 HTML 而不是 JSON
        if response.text.strip().startswith('<'):
            print("[!] crt.sh 返回了 HTML 页面而非 JSON，可能被限流或服务异常")
            print(f"    响应预览: {response.text[:200]}...")
            return
        
        data = response.json()
    except requests.exceptions.Timeout:
        print("[!] 连接 crt.sh 超时，请检查网络或稍后重试")
        return
    except requests.exceptions.RequestException as e:
        print(f"[!] 网络请求失败: {e}")
        return
    except Exception as e:
        print(f"[!] 解析 JSON 失败: {e}")
        print(f"    响应预览: {response.text[:200]}...")
        return

    # 按 ID 倒序排列 (ID越大代表越新)
    # 注意：有时候 ID 大的不一定 not_before 晚，但通常是对应的
    sorted_certs = sorted(data, key=lambda x: x['id'], reverse=True)

    print(f"[*] 找到 {len(sorted_certs)} 张证书。正在尝试计算最新的 3 张...\n")

    # 我们尝试最新的 3 张，以防万一“最后一张”指的是列表里的特定某张
    for i, entry in enumerate(sorted_certs[:5]):
        cert_id = entry['id']
        common_name = entry.get('common_name', 'Unknown')
        issuer_name = entry.get('issuer_name', 'Unknown')
        
        # 排除非 ip6.arpa 的干扰项 (有时候模糊搜索会混入)
        if 'ip6.arpa' not in common_name and 'ip6.arpa' not in entry.get('name_value', ''):
            continue

        print(f"--- 候选证书 #{i+1} (ID: {cert_id}) ---")
        print(f"   颁发者: {issuer_name}")
        print(f"   时间: {entry.get('not_before', 'Unknown')}")

        # 下载证书内容
        try:
            cert_pem_url = f"https://crt.sh/?d={cert_id}"
            cert_resp = requests.get(cert_pem_url, timeout=10)
            cert_data = cert_resp.content
            
            # 加载证书
            cert = load_pem_x509_certificate(cert_data, default_backend())
            public_key = cert.public_key()

            # 检查公钥是否是 P-256 (题目要求)
            if not isinstance(public_key, ec.EllipticCurvePublicKey) or not isinstance(public_key.curve, ec.SECP256R1):
                print("   [x] 跳过：公钥不是 P-256 曲线")
                continue

            # 3. 进行 ECDH 密钥交换
            # 共享秘密 S = d * Q
            # shared_key 返回的是 S 点的 x 坐标
            shared_key = private_key.exchange(ec.ECDH(), public_key)
            
            # 取前 3 个字节
            result_hex = shared_key[:3].hex()
            print(f"   [!] 共享秘密前3字节: >>> {result_hex} <<<")
            
        except Exception as e:
            print(f"   [!] 处理证书出错: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    solve_puzzle()
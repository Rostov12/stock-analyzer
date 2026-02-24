import oci
import time
import sys
from datetime import datetime

# ==========================================
# Oracle Cloud ARM 搶機腳本 (Oracle Sniper)
# ==========================================

# 硬體規格設定 (ARM 4核 24G)
SHAPE = "VM.Standard.A1.Flex"
CPUS = 4.0
MEMORY = 24.0

def launch_instance(compute_client, config, ad_name):
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 嘗試在 {ad_name} 建立實例...")
        
        response = compute_client.launch_instance(
            oci.core.models.LaunchInstanceDetails(
                compartment_id=config["tenancy"],
                availability_domain=ad_name,
                shape=SHAPE,
                shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                    ocpus=CPUS,
                    memory_in_gbs=MEMORY
                ),
                image_id=config["image_id"],
                create_vnic_details=oci.core.models.CreateVnicDetails(
                    subnet_id=config["subnet_id"],
                    assign_public_ip=True
                ),
                display_name="Crypto-Monitor-Server",
                metadata={
                    "ssh_authorized_keys": config["ssh_public_key"]
                }
            )
        )
        print(f"✅ 成功！機器已在 {ad_name} 開始建置。")
        return True
    except oci.exceptions.ServiceError as e:
        if e.status == 429 or "Out of capacity" in str(e).lower() or "limit" in str(e).lower():
            print(f"❌ {ad_name} 目前無庫存...")
        else:
            print(f"⚠️ 發生錯誤 ({ad_name}): {e.message}")
        return False

def main():
    # 讀取 ~/.oci/config 檔案
    try:
        config_data = oci.config.from_file()
        compute_client = oci.core.ComputeClient(config_data)
        
        # 可用性網域清單 (由使用者提供)
        AD_LIST = [
            "XWdY:PHX-AD-1",
            "XWdY:PHX-AD-2",
            "XWdY:PHX-AD-3"
        ]
        
        # 這些 OCID 需要使用者提供
        custom_config = {
            "tenancy": config_data["tenancy"],
            "image_id": "ocid1.image.oc1.phx.aaaaaaaaco6alg4pynu7quhi6jccf35q2exwkqfx2xpr7xbosk5kesiflx6q",
            "subnet_id": "ocid1.subnet.oc1.phx.aaaaaaaavywmwjvs46njqg66wyvom7yqntchgrrhbxgw7wr23lg3wgbs4umq",
            "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7jqcGAzIa/99O3Or+Ov/0a6aWfuvkPJguIxgtoQpmbFk2F3U9dUy+MX61R270Mz8Z1tYDkYQ14fNXVUPooIFXGr4RKaA56gRLgeT+w5aTJtPXp6bsQvRwz/E4f95ayJTH+wvEKhrux13jEBQrZeqpVldTHGGnndv6XUQEpb3UHkfzPYAEdcSlcDGS3X3lykLRiWJ+CToAiWQ++jpvJvGFrDU1F/fyoM0c6ry2U/AdNP6uBydQ0tWm76wr+ICUk+2RoeXY/r5w51RFQu54/3pyb4C8lYUPZH54ySZ13l5uXzmQepKwgTIHGZRYRBPNSg5gGGGM6rMBMYJlhgAmA/yF ssh-key-2026-02-24"
        }
        
        interval = 30 # 每 30 秒輪詢一次
        
        print("🚀 Oracle Sniper 已啟動，開始對鳳凰城三個 AD 進行巡迴搶機...")
        
        while True:
            for ad in AD_LIST:
                success = launch_instance(compute_client, custom_config, ad)
                if success:
                    print("🎉 恭喜！搶機成功。")
                    sys.exit(0)
                time.sleep(2) # 每個 AD 之間稍微停頓
            
            print(f"😴 所有 AD 暫無貨，休息 {interval} 秒...")
            time.sleep(interval)
            
    except Exception as e:
        print(f"💥 啟動失敗: {str(e)}")

if __name__ == "__main__":
    main()

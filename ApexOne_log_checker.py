#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ApexOne Log Checker
OfficeScan管理コンソールにアクセスしてシステムイベントログを取得するツール
"""

import sys
import locale
import json
import os
import base64
from cryptography.fernet import Fernet
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright

# 文字エンコーディング設定
def setup_encoding():
    """文字エンコーディング設定を初期化"""
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
        
        if sys.platform.startswith('win'):
            locale.setlocale(locale.LC_ALL, 'Japanese_Japan.932')
        else:
            locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
            
        print("✅ 文字エンコーディング設定完了")
        print(f"   標準出力: {sys.stdout.encoding}")
        print(f"   標準エラー: {sys.stderr.encoding}")
        print(f"   ロケール: {locale.getlocale()}")
        
    except Exception as e:
        print(f"⚠️ 文字エンコーディング設定エラー: {e}")
        print("💡 デフォルト設定で続行します")

# 文字エンコーディング設定を実行
setup_encoding()

class ApexOneLogChecker:
    def __init__(self):
        self.target_url = "https://pcvtmu53:4343/officescan/"
        self.credentials_file = "secure_credentials.enc"
        self.key_file = "encryption_key.key"
        self.log_file = "apexone_log_checker.log"
        self.debug_port = 9222
        self.user_data_dir = r"C:\Users\1040120\chrome_debug_profile"
        self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
    def generate_encryption_key(self):
        """暗号化キーを生成"""
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as key_file:
                key_file.write(key)
            print(f"🔑 新しい暗号化キーを生成しました: {self.key_file}")
        else:
            with open(self.key_file, 'rb') as key_file:
                key = key_file.read()
        return key
    
    def encrypt_credentials(self, username, password):
        """認証情報を暗号化して保存"""
        try:
            key = self.generate_encryption_key()
            fernet = Fernet(key)
            
            credentials = {
                'username': username,
                'password': password,
                'created_at': datetime.now().isoformat()
            }
            
            encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            print("🔐 認証情報を暗号化して保存しました")
            return True
            
        except Exception as e:
            print(f"❌ 認証情報の暗号化に失敗: {e}")
            return False
    
    def decrypt_credentials(self):
        """保存された認証情報を復号化"""
        try:
            if not os.path.exists(self.credentials_file):
                return None
            
            with open(self.key_file, 'rb') as key_file:
                key = key_file.read()
            
            fernet = Fernet(key)
            
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            print("🔓 保存された認証情報を復号化しました")
            return credentials
            
        except Exception as e:
            print(f"❌ 認証情報の復号化に失敗: {e}")
            return None
    
    def get_manual_credentials(self):
        """手動で認証情報を入力"""
        print("\n🔐 初回アクセスのため、認証情報を入力してください")
        print("=" * 50)
        
        username = input("ユーザー名: ").strip()
        password = input("パスワード: ").strip()
        
        if not username or not password:
            print("❌ ユーザー名とパスワードは必須です")
            return None
        
        # 認証情報を暗号化して保存
        if self.encrypt_credentials(username, password):
            return {'username': username, 'password': password}
        else:
            return None
    
    def log_event(self, message, level="INFO"):
        """イベントをログファイルに記録"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            print(f"⚠️ ログ記録エラー: {e}")
    
    async def start_chrome_debug(self):
        """Chromeデバッグモードを起動"""
        try:
            print("🚀 Chromeデバッグモード起動中...")
            
            # Chromeプロセスが既に起動しているかチェック
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.debug_port))
            sock.close()
            
            if result == 0:
                print(f"✅ Chromeデバッグポート({self.debug_port})が既に利用可能です")
                return True
            
            # Chrome実行ファイルの存在確認
            if not os.path.exists(self.chrome_exe):
                print(f"❌ Chrome実行ファイルが見つかりません: {self.chrome_exe}")
                return False
            
            # Chromeデバッグモードで起動
            chrome_args = [
                self.chrome_exe,
                f"--remote-debugging-port={self.debug_port}",
                f"--user-data-dir={self.user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-web-security",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--ignore-certificate-errors-spki-list",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",
                "--disable-javascript",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *chrome_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Chromeの起動を待つ
            await asyncio.sleep(3)
            
            # ポートが利用可能になるまで待つ
            max_wait = 30
            for i in range(max_wait):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', self.debug_port))
                sock.close()
                
                if result == 0:
                    print(f"✅ Chromeデバッグポート({self.debug_port})が利用可能になりました")
                    return True
                
                await asyncio.sleep(1)
            
            print(f"❌ Chromeデバッグポート({self.debug_port})の起動に失敗しました")
            return False
            
        except Exception as e:
            print(f"❌ Chromeデバッグモード起動エラー: {e}")
            return False
    
    async def check_system_logs(self):
        """システムイベントログをチェック"""
        try:
            print(f"🎯 OfficeScan管理コンソールにアクセス: {self.target_url}")
            
            # 認証情報の取得
            credentials = self.decrypt_credentials()
            if not credentials:
                credentials = self.get_manual_credentials()
                if not credentials:
                    return False
            
            # Chromeデバッグモードを起動
            if not await self.start_chrome_debug():
                return False
            
            async with async_playwright() as p:
                # 既存のChromeに接続
                browser = await p.chromium.connect_over_cdp(f"http://localhost:{self.debug_port}")
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = context.pages[0] if context.pages else await context.new_page()
                
                print("📋 ステップ1: OfficeScan管理コンソールにアクセス中...")
                await page.goto(self.target_url, wait_until='networkidle', timeout=30000)
                
                # ログインフォームの確認
                try:
                    username_input = await page.wait_for_selector('input[name="username"], input[type="text"]', timeout=10000)
                    password_input = await page.wait_for_selector('input[name="password"], input[type="password"]', timeout=10000)
                    
                    print("📋 ステップ2: ログイン情報を入力中...")
                    await username_input.fill(credentials['username'])
                    await password_input.fill(credentials['password'])
                    
                    # ログインボタンをクリック
                    login_button = await page.wait_for_selector('input[type="submit"], button[type="submit"], .login-button', timeout=10000)
                    await login_button.click()
                    
                    print("📋 ステップ3: ログイン処理中...")
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    
                except Exception as e:
                    print(f"⚠️ ログインフォームが見つからないか、既にログイン済み: {e}")
                
                print("📋 ステップ4: ログメニューにアクセス中...")
                
                # ログメニューを探す
                log_menu_selectors = [
                    'a[href*="log"]',
                    'a:has-text("ログ")',
                    '.log-menu',
                    'nav a:has-text("ログ")',
                    'ul li a:has-text("ログ")'
                ]
                
                log_menu = None
                for selector in log_menu_selectors:
                    try:
                        log_menu = await page.wait_for_selector(selector, timeout=5000)
                        if log_menu:
                            break
                    except:
                        continue
                
                if not log_menu:
                    print("❌ ログメニューが見つかりません")
                    return False
                
                await log_menu.click()
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                print("📋 ステップ5: システムイベントメニューを選択中...")
                
                # システムイベントメニューを探す
                system_event_selectors = [
                    'a:has-text("システムイベント")',
                    'a[href*="system"]',
                    'a[href*="event"]',
                    '.system-event-menu',
                    'li a:has-text("システムイベント")'
                ]
                
                system_event_menu = None
                for selector in system_event_selectors:
                    try:
                        system_event_menu = await page.wait_for_selector(selector, timeout=5000)
                        if system_event_menu:
                            break
                    except:
                        continue
                
                if not system_event_menu:
                    print("❌ システムイベントメニューが見つかりません")
                    return False
                
                await system_event_menu.click()
                await page.wait_for_load_state('networkidle', timeout=15000)
                
                print("📋 ステップ6: システムイベントログを取得中...")
                
                # ログテーブルを探す
                log_table_selectors = [
                    'table',
                    '.log-table',
                    '.event-table',
                    'div[class*="table"]',
                    'div[class*="grid"]'
                ]
                
                log_table = None
                for selector in log_table_selectors:
                    try:
                        log_table = await page.wait_for_selector(selector, timeout=10000)
                        if log_table:
                            break
                    except:
                        continue
                
                if not log_table:
                    print("❌ ログテーブルが見つかりません")
                    return False
                
                # 最新のログ行を取得
                try:
                    # テーブルの行を取得
                    rows = await log_table.query_selector_all('tr')
                    
                    if len(rows) > 1:  # ヘッダー行 + データ行
                        latest_row = rows[-1]  # 最新行
                        row_text = await latest_row.inner_text()
                        
                        print("\n" + "="*60)
                        print("📊 最新のシステムイベントログ:")
                        print("="*60)
                        print(row_text)
                        print("="*60)
                        
                        # ログに記録
                        self.log_event(f"最新システムイベントログ取得: {row_text[:100]}...")
                        
                        # スクリーンショットを保存
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = f"system_event_log_{timestamp}.png"
                        await page.screenshot(path=screenshot_path)
                        print(f"📸 スクリーンショットを保存: {screenshot_path}")
                        
                        return True
                    else:
                        print("❌ ログデータが見つかりません")
                        return False
                        
                except Exception as e:
                    print(f"❌ ログデータの取得に失敗: {e}")
                    return False
                
        except Exception as e:
            print(f"❌ システムログチェックエラー: {e}")
            self.log_event(f"エラー: {e}", "ERROR")
            return False
    
    async def run(self):
        """メイン実行関数"""
        print("🚀 ApexOne Log Checker 開始")
        print("=" * 50)
        
        self.log_event("ApexOne Log Checker 開始")
        
        success = await self.check_system_logs()
        
        if success:
            print("\n✅ システムイベントログの取得が完了しました")
            self.log_event("システムイベントログ取得完了")
        else:
            print("\n❌ システムイベントログの取得に失敗しました")
            self.log_event("システムイベントログ取得失敗", "ERROR")
        
        print("\n" + "=" * 50)
        print("🏁 ApexOne Log Checker 終了")

async def main():
    """メイン関数"""
    checker = ApexOneLogChecker()
    await checker.run()

if __name__ == "__main__":
    asyncio.run(main())

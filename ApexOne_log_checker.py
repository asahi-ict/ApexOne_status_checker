#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ApexOne Log Checker
OfficeScan管理コンソールにアクセスしてシステムイベントログを取得するツール
"""

import json
import os
from cryptography.fernet import Fernet
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright

class ApexOneLogChecker:
    def __init__(self):
        # 複数のサーバーURL
        self.servers = [
            "https://pcvtmu53:4343/officescan/",
            "https://pcvtmu54:4343/officescan/"
        ]
        self.credentials_file = "secure_credentials.enc"
        self.key_file = "encryption_key.key"
        self.debug_port = 9222

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
    
    def encrypt_credentials(self, username, password, domain):
        """認証情報を暗号化して保存"""
        try:
            key = self.generate_encryption_key()
            fernet = Fernet(key)
            
            credentials = {
                'username': username,
                'password': password,
                'domain': domain,
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
        domain = input("ドメイン (tad.asahi-np.co.jp): ").strip()
        
        # ドメインが空の場合はデフォルト値を設定
        if not domain:
            domain = "tad.asahi-np.co.jp"
        
        if not username or not password:
            print("❌ ユーザー名とパスワードは必須です")
            return None
        
        # 認証情報を暗号化して保存
        if self.encrypt_credentials(username, password, domain):
            return {'username': username, 'password': password, 'domain': domain}
        else:
            return None

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
            
            # デバッグポートが利用できない場合は、新しいChromeインスタンスを起動
            print(f"⚠️ Chromeデバッグポート({self.debug_port})が利用できません")
            print("🔄 新しいChromeインスタンスをデバッグモードで起動中...")
            
            import subprocess
            import platform
            
            # Chromeの実行パスを特定
            chrome_paths = []
            if platform.system() == "Windows":
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
                    "chrome.exe"  # PATHから検索
                ]
            
            chrome_exe = None
            for path in chrome_paths:
                try:
                    if os.path.exists(path):
                        chrome_exe = path
                        break
                    elif path == "chrome.exe":
                        # PATHから検索
                        result = subprocess.run(["where", "chrome.exe"], capture_output=True, text=True)
                        if result.returncode == 0:
                            chrome_exe = "chrome.exe"
                            break
                except:
                    continue
            
            if not chrome_exe:
                print("❌ Chromeの実行ファイルが見つかりません")
                print("💡 手動でChromeを起動してください:")
                print(f"   chrome.exe --remote-debugging-port={self.debug_port}")
                return False
            
            # デバッグ用のユーザーデータディレクトリを作成
            debug_user_data_dir = os.path.join(os.getcwd(), "chrome_debug_profile")
            os.makedirs(debug_user_data_dir, exist_ok=True)
            
            # Chromeをデバッグモードで起動
            chrome_args = [
                chrome_exe,
                f"--remote-debugging-port={self.debug_port}",
                f"--user-data-dir={debug_user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
            
            try:
                # 非同期でChromeを起動
                process = subprocess.Popen(
                    chrome_args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0
                )
                
                print(f"✅ Chromeプロセスを起動しました (PID: {process.pid})")
                
                # デバッグポートが利用可能になるまで待機
                print("⏳ デバッグポートの準備を待機中...")
                for attempt in range(30):  # 最大30秒待機
                    await asyncio.sleep(1)
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        result = sock.connect_ex(('localhost', self.debug_port))
                        sock.close()
                        if result == 0:
                            print(f"✅ Chromeデバッグポート({self.debug_port})が利用可能になりました")
                            return True
                    except:
                        continue
                
                print("❌ デバッグポートの準備がタイムアウトしました")
                return False
                
            except Exception as e:
                print(f"❌ Chrome起動エラー: {e}")
                print("💡 手動でChromeを起動してください:")
                print(f"   chrome.exe --remote-debugging-port={self.debug_port}")
                return False
            
        except Exception as e:
            print(f"❌ Chromeデバッグモード起動エラー: {e}")
            return False
    
    async def check_system_logs_for_server(self, server_url):
        """指定されたサーバーでシステムイベントログをチェック"""
        try:
            print(f"🎯 OfficeScan管理コンソールにアクセス: {server_url}")
            
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
                
                # SSL証明書の検証を無効にしたコンテキストを作成
                context = await browser.new_context(ignore_https_errors=True)
                page = await context.new_page()
                
                print("📋 ステップ1: OfficeScan管理コンソールにアクセス中...")
                await page.goto(server_url, wait_until='networkidle', timeout=30000)
                
                # ログインフォームの確認
                try:
                    # ドメイン選択フィールドを探す
                    domain_selectors = [
                        'select#labelDomain',
                        'select[name="domainlist"]',
                        'select[name="domain"]',
                        'select[id*="domain"]',
                        'select[class*="domain"]'
                    ]
                    
                    domain_select = None
                    for selector in domain_selectors:
                        try:
                            domain_select = await page.wait_for_selector(selector, timeout=5000)
                            if domain_select:
                                print(f"✅ ドメイン選択フィールドを発見: {selector}")
                                break
                        except:
                            continue
                    
                    if domain_select:
                        print("📋 ステップ2a: ドメインを選択中...")
                        try:
                            await domain_select.select_option(value="tad.asahi-np.co.jp")
                            print("✅ ドメイン選択完了: tad.asahi-np.co.jp")
                        except Exception as select_error:
                            print(f"⚠️ ドメイン選択エラー: {select_error}")
                            # 代替方法: テキストで選択
                            try:
                                await domain_select.select_option(label="tad.asahi-np.co.jp")
                                print("✅ ドメイン選択完了（代替方法）: tad.asahi-np.co.jp")
                            except Exception as alt_error:
                                print(f"❌ ドメイン選択失敗: {alt_error}")
                    else:
                        print("⚠️ ドメイン選択フィールドが見つかりません")
                    
                    # ユーザー名とパスワードフィールドを探す
                    username_input = await page.wait_for_selector('input#labelUsername, input[name="username"]', timeout=10000)
                    password_input = await page.wait_for_selector('input#labelPassword, input[name="password"]', timeout=10000)
                    
                    print("📋 ステップ2b: ログイン情報を入力中...")
                    await username_input.fill(credentials['username'])
                    await password_input.fill(credentials['password'])
                    
                    # ログインボタンをクリック
                    login_button_selectors = [
                        'button#btn-signin',
                        'button[rel="btn_signin"]',
                        'button:has-text("ログオン")',
                        'button:has-text("ログイン")',
                        'input[type="submit"]',
                        'button[type="submit"]',
                        '.login-button'
                    ]
                    
                    login_button = None
                    for selector in login_button_selectors:
                        try:
                            login_button = await page.wait_for_selector(selector, timeout=5000)
                            if login_button:
                                print(f"✅ ログインボタンを発見: {selector}")
                                break
                        except:
                            continue
                    
                    if login_button:
                        print("📋 ステップ2c: ログインボタンをクリック中...")
                        await login_button.click()
                        print("✅ ログインボタンクリック完了")
                        
                        # ログイン処理の完了を待つ
                        print("📋 ステップ2d: ログイン処理の完了を待機中...")
                        await asyncio.sleep(2)
                        
                        # ページのURLを確認
                        current_url = page.url
                        print(f"📍 現在のURL: {current_url}")
                        
                    else:
                        print("❌ ログインボタンが見つかりません")
                        return False
                    
                    print("📋 ステップ3: ログイン処理中...")
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    
                    # ログイン成功の確認
                    try:
                        html_content = await page.content()
                        if "ログオン" in html_content and "form_login" in html_content:
                            print("⚠️ ログイン画面が残存しています。認証に失敗した可能性があります")
                            return False
                        else:
                            print("✅ ログイン成功を確認しました")
                            
                    except Exception as e:
                        print(f"⚠️ ログイン確認エラー: {e}")
                        return False
                    
                except Exception as e:
                    print(f"⚠️ ログインフォームが見つからないか、既にログイン済み: {e}")
                    return False
                
                # ログイン完了後、直接ログページにアクセス
                print("📋 ステップ4: システムイベントログページに直接アクセス中...")
                
                # サーバーURLからベースURLを取得してシステムイベントログURLを構築
                base_url = server_url.rstrip('/')
                system_event_url = f"{base_url}/console/html/cgi/cgiShowLogs.exe?id=12015"
                
                try:
                    # 新しいページでシステムイベントログページにアクセス
                    log_page = await context.new_page()
                    await log_page.goto(system_event_url, wait_until='networkidle', timeout=30000)
                    print(f"✅ システムイベントログページにアクセス: {system_event_url}")
                    
                    # ログテーブルを探す
                    print("📋 ステップ6b: ログテーブルを検索中...")
                    log_table_selectors = [
                        'table',
                        '.log-table',
                        '.event-table',
                        'div[class*="table"]',
                        'div[class*="grid"]',
                        'table[class*="log"]',
                        'table[class*="event"]',
                        '.data-table',
                        '.result-table',
                        'table[class*="system"]',
                        'div[class*="log"]',
                        'div[class*="event"]',
                        'div[class*="system"]'
                    ]
                    
                    log_table = None
                    for selector in log_table_selectors:
                        try:
                            log_table = await log_page.wait_for_selector(selector, timeout=5000)
                            if log_table:
                                print(f"✅ ログテーブルを発見: {selector}")
                                break
                        except:
                            continue
                    
                    if not log_table:
                        print("❌ ログテーブルが見つかりません")
                        return False
                    
                    # ログテーブル内で特定の文言を検索
                    print("📋 ステップ7: ログテーブル内で特定の文言を検索中...")
                    
                    # テーブルの行を取得
                    rows = await log_table.query_selector_all('tr')
                    
                    if len(rows) > 1:  # ヘッダー行 + データ行
                        target_text = "次の役割を使用してログインしました"
                        
                        print(f"🔍 検索対象文言: '{target_text}'")
                        print(f"📊 検索対象行数: {len(rows)}行")
                        
                        # 各行のテキストを取得して検索（最初の行が最新）
                        latest_found = None
                        found_count = 0
                        
                        for i, row in enumerate(rows):
                            try:
                                row_text = await row.inner_text()
                                if target_text in row_text:
                                    found_count += 1
                                    # 最初に見つかった行が最新なので、初回のみ設定
                                    if latest_found is None:
                                        latest_found = {
                                            'index': i,
                                            'text': row_text
                                        }
                                        print(f"✅ 最新の該当文言を発見: 行{i+1}")
                                    # 2回目以降は件数のみカウント（最新は更新しない）
                            except Exception as row_error:
                                print(f"⚠️ 行{i+1}のテキスト取得エラー: {row_error}")
                                continue
                        
                        if latest_found:
                            print(f"\n" + "="*60)
                            print(f"📊 最新のログイン役割ログ")
                            print("="*60)
                            print(f"発見件数: {found_count}件")
                            print(f"最新ログ: 行{latest_found['index']+1}")
                            print("="*60)
                            print(latest_found['text'])
                            print("="*60)
                            
                            return True
                        else:
                            print(f"❌ '{target_text}' を含むログが見つかりませんでした")
                            
                            # 最新のログ行を表示（参考用）
                            latest_row = rows[-1]
                            latest_text = await latest_row.inner_text()
                            print(f"\n📋 最新のログ（参考）:")
                            print(latest_text[:200] + "..." if len(latest_text) > 200 else latest_text)
                            
                            return False
                    else:
                        print("❌ ログデータが見つかりません")
                        return False
                        
                except Exception as e:
                    print(f"❌ ログページアクセスエラー: {e}")
                    return False
                
        except Exception as e:
            print(f"❌ システムログチェックエラー: {e}")
            return False
    
    async def check_system_logs(self):
        """全てのサーバーでシステムイベントログをチェック"""
        print("🚀 ApexOne Log Checker 開始")
        print("="*50)
        
        all_results = []
        
        for i, server_url in enumerate(self.servers, 1):
            print(f"\n📊 サーバー {i}/{len(self.servers)}: {server_url}")
            print("-" * 50)
            
            try:
                result = await self.check_system_logs_for_server(server_url)
                all_results.append({
                    'server': server_url,
                    'success': result,
                    'timestamp': datetime.now()
                })
                
                if result:
                    print(f"✅ サーバー {i} の処理が完了しました")
                else:
                    print(f"❌ サーバー {i} の処理に失敗しました")
                    
            except Exception as e:
                print(f"❌ サーバー {i} でエラーが発生: {e}")
                all_results.append({
                    'server': server_url,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
            
            # 次のサーバーに進む前に少し待機
            if i < len(self.servers):
                print("⏳ 次のサーバーに進む前に待機中...")
                await asyncio.sleep(2)
        
        # 結果サマリーを表示
        print(f"\n" + "="*60)
        print("📊 全サーバー処理結果サマリー")
        print("="*60)
        
        success_count = 0
        for i, result in enumerate(all_results, 1):
            server_name = result['server'].split('//')[1].split(':')[0]
            status = "✅ 成功" if result['success'] else "❌ 失敗"
            print(f"サーバー {i} ({server_name}): {status}")
            if result['success']:
                success_count += 1
        
        print(f"\n成功: {success_count}/{len(self.servers)} サーバー")
        print("="*60)
        
        return success_count > 0
    
    async def run(self):
        """メイン実行関数"""
        success = await self.check_system_logs()
        
        if success:
            print("\n✅ システムイベントログの取得が完了しました")
        else:
            print("\n❌ システムイベントログの取得に失敗しました")
        
        print("\n" + "=" * 50)
        print("🏁 ApexOne Log Checker 終了")

async def main():
    """メイン関数"""
    checker = ApexOneLogChecker()
    await checker.run()

if __name__ == "__main__":
    asyncio.run(main())

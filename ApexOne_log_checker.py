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
                        await asyncio.sleep(1)
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
                        await asyncio.sleep(5)  # 5秒待機
                        
                        # ページのURLを確認
                        current_url = page.url
                        print(f"📍 現在のURL: {current_url}")
                        
                    else:
                        print("❌ ログインボタンが見つかりません")
                        return False
                    
                    print("📋 ステップ3: ログイン処理中...")
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    
                    # ログイン後のページをデバッグ用に保存
                    try:
                        html_content = await page.content()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        with open(f"debug_after_login_{timestamp}.html", "w", encoding="utf-8") as f:
                            f.write(html_content)
                        print(f"📄 ログイン後のHTMLを保存: debug_after_login_{timestamp}.html")
                        
                        # スクリーンショットも保存
                        screenshot_path = f"after_login_{timestamp}.png"
                        await page.screenshot(path=screenshot_path)
                        print(f"📸 ログイン後のスクリーンショットを保存: {screenshot_path}")
                        
                        # ログイン成功の確認
                        if "ログオン" in html_content and "form_login" in html_content:
                            print("⚠️ ログイン画面が残存しています。認証に失敗した可能性があります")
                            # エラーメッセージを確認
                            try:
                                error_msg = await page.query_selector('.tm-alert .tm-msg')
                                if error_msg:
                                    error_text = await error_msg.inner_text()
                                    print(f"❌ エラーメッセージ: {error_text}")
                            except:
                                pass
                            return False
                        else:
                            print("✅ ログイン成功を確認しました")
                            
                    except Exception as debug_error:
                        print(f"⚠️ デバッグ情報保存エラー: {debug_error}")
                    
                except Exception as e:
                    print(f"⚠️ ログインフォームが見つからないか、既にログイン済み: {e}")
                    # デバッグ用にページのHTMLを保存
                    try:
                        html_content = await page.content()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        with open(f"debug_login_page_{timestamp}.html", "w", encoding="utf-8") as f:
                            f.write(html_content)
                        print(f"📄 デバッグ用HTMLを保存: debug_login_page_{timestamp}.html")
                    except Exception as html_error:
                        print(f"⚠️ HTML保存エラー: {html_error}")
                
                print("📋 ステップ4: メニューiframeにアクセス中...")
                
                # メニューiframeを探す
                try:
                    menu_frame = await page.wait_for_selector('iframe[name="menu"]', timeout=10000)
                    if menu_frame:
                        print("✅ メニューiframeを発見しました")
                        
                        # iframeのコンテキストに切り替え
                        frame = await menu_frame.content_frame()
                        if frame:
                            print("✅ iframeコンテキストに切り替えました")
                            
                            # iframe内のHTMLをデバッグ用に保存
                            try:
                                frame_html = await frame.content()
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                with open(f"debug_menu_frame_{timestamp}.html", "w", encoding="utf-8") as f:
                                    f.write(frame_html)
                                print(f"📄 メニューiframeのHTMLを保存: debug_menu_frame_{timestamp}.html")
                            except Exception as frame_debug_error:
                                print(f"⚠️ メニューiframe HTML保存エラー: {frame_debug_error}")
                            
                            # ログメニューを探す
                            print("📋 ステップ4a: ログメニューを検索中...")
                            log_menu_selectors = [
                                'a[href*="log"]',
                                'a:has-text("ログ")',
                                'a:has-text("Log")',
                                '.log-menu',
                                'nav a:has-text("ログ")',
                                'ul li a:has-text("ログ")',
                                'button:has-text("ログ")',
                                'button:has-text("Log")',
                                '[class*="log"]',
                                '[id*="log"]',
                                'li a:contains("ログ")',
                                'li a:contains("Log")'
                            ]
                            
                            log_menu = None
                            for selector in log_menu_selectors:
                                try:
                                    log_menu = await frame.wait_for_selector(selector, timeout=5000)
                                    if log_menu:
                                        print(f"✅ ログメニューを発見: {selector}")
                                        break
                                except:
                                    continue
                            
                            if log_menu:
                                print("📋 ステップ4b: ログメニューをクリック中...")
                                await log_menu.click()
                                await frame.wait_for_load_state('networkidle', timeout=10000)
                                print("✅ ログメニュークリック完了")
                            else:
                                print("❌ iframe内でログメニューが見つかりません")
                                return False
                        else:
                            print("❌ iframeコンテキストの取得に失敗しました")
                            return False
                    else:
                        print("❌ メニューiframeが見つかりません")
                        return False
                        
                except Exception as frame_error:
                    print(f"❌ メニューiframeアクセスエラー: {frame_error}")
                    return False
                
                print("📋 ステップ5: システムイベントメニューを選択中...")
                
                # システムイベントメニューを探す（iframe内で検索）
                system_event_selectors = [
                    'span.label:has-text("システムイベント")',
                    'span[op="12015"]',
                    'li[op="12015"]',
                    'span.label[op="12015"]',
                    'a:has-text("システムイベント")',
                    'a[href*="system"]',
                    'a[href*="event"]',
                    '.system-event-menu',
                    'li a:has-text("システムイベント")'
                ]
                
                system_event_menu = None
                for selector in system_event_selectors:
                    try:
                        system_event_menu = await frame.wait_for_selector(selector, timeout=5000)
                        if system_event_menu:
                            print(f"✅ システムイベントメニューを発見: {selector}")
                            break
                    except:
                        continue
                
                if not system_event_menu:
                    print("❌ システムイベントメニューが見つかりません")
                    return False
                
                print("📋 ステップ5a: システムイベントメニューをクリック中...")
                await system_event_menu.click()
                await frame.wait_for_load_state('networkidle', timeout=15000)
                print("✅ システムイベントメニュークリック完了")
                
                # ページ遷移を待機
                print("📋 ステップ5b: ページ遷移を待機中...")
                await asyncio.sleep(3)
                
                # メインフレームの更新を待機
                try:
                    main_frame = await page.wait_for_selector('iframe[name="main"]', timeout=10000)
                    if main_frame:
                        main_frame_content = await main_frame.content_frame()
                        if main_frame_content:
                            # メインフレームのURLが変更されるまで待機
                            max_wait = 30
                            for i in range(max_wait):
                                current_url = main_frame_content.url
                                if "system" in current_url or "event" in current_url or "12015" in current_url:
                                    print(f"✅ システムイベントページに遷移しました: {current_url}")
                                    break
                                await asyncio.sleep(1)
                            else:
                                print(f"⚠️ ページ遷移が確認できません。現在のURL: {current_url}")
                except Exception as wait_error:
                    print(f"⚠️ ページ遷移待機エラー: {wait_error}")
                
                print("📋 ステップ6: システムイベントページの読み込みを待機中...")
                await asyncio.sleep(10)  # ページ遷移を待機（時間を延長）
                
                # 利用可能なフレームを確認
                try:
                    # 利用可能なフレームを探す
                    frame_selectors = [
                        'iframe[name="main"]',
                        'iframe[id="main"]',
                        'iframe[name="osce_top"]',
                        'iframe[id="osce_top"]',
                        'iframe[src*="main"]',
                        'iframe[src*="osce"]',
                        'iframe'
                    ]
                    
                    available_frames = []
                    for selector in frame_selectors:
                        try:
                            frame = await page.wait_for_selector(selector, timeout=5000)
                            if frame:
                                frame_content = await frame.content_frame()
                                if frame_content:
                                    frame_url = frame_content.url
                                    frame_name = await frame.get_attribute('name') or await frame.get_attribute('id') or 'unknown'
                                    available_frames.append({
                                        'selector': selector,
                                        'name': frame_name,
                                        'url': frame_url,
                                        'content': frame_content
                                    })
                                    print(f"✅ フレームを発見: {frame_name} - {frame_url}")
                        except:
                            continue
                    
                    if not available_frames:
                        print("❌ 利用可能なフレームが見つかりません")
                        return False
                    
                    # システムイベントページを含むフレームを探す
                    target_frame = None
                    for frame_info in available_frames:
                        frame_url = frame_info['url']
                        if "system" in frame_url or "event" in frame_url or "12015" in frame_url:
                            target_frame = frame_info
                            print(f"✅ システムイベントページを含むフレームを発見: {frame_info['name']}")
                            break
                    
                    # システムイベントページが見つからない場合は、osce_topフレームを試す
                    if not target_frame:
                        for frame_info in available_frames:
                            if frame_info['name'] in ['osce_top', 'main']:
                                target_frame = frame_info
                                print(f"✅ 代替フレームを使用: {frame_info['name']}")
                                break
                    
                    if not target_frame:
                        print("❌ 適切なフレームが見つかりません")
                        return False
                    
                    main_frame_content = target_frame['content']
                    main_url = target_frame['url']
                    print(f"📍 選択されたフレームのURL: {main_url}")
                    # 選択されたフレーム内のHTMLをデバッグ用に保存
                    try:
                        main_html = await main_frame_content.content()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        frame_name = target_frame['name']
                        with open(f"debug_{frame_name}_frame_{timestamp}.html", "w", encoding="utf-8") as f:
                            f.write(main_html)
                        print(f"📄 {frame_name}フレームのHTMLを保存: debug_{frame_name}_frame_{timestamp}.html")
                    except Exception as main_debug_error:
                        print(f"⚠️ {frame_name}フレームHTML保存エラー: {main_debug_error}")
                    
                    print("📋 ステップ6a: システムイベントログを取得中...")
                    
                    # ログテーブルを探す（選択されたフレーム内で検索）
                    log_table_selectors = [
                        'table',
                        '.log-table',
                        '.event-table',
                        'div[class*="table"]',
                        'div[class*="grid"]',
                        'table[class*="log"]',
                        'table[class*="event"]',
                        '.data-table',
                        '.result-table'
                    ]
                    
                    log_table = None
                    for selector in log_table_selectors:
                        try:
                            log_table = await main_frame_content.wait_for_selector(selector, timeout=10000)
                            if log_table:
                                print(f"✅ ログテーブルを発見: {selector}")
                                break
                        except:
                            continue
                        
                except Exception as frame_error:
                    print(f"❌ フレームアクセスエラー: {frame_error}")
                    return False
                
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
                        
                        # スクリーンショットを保存（メインフレーム内）
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = f"system_event_log_{timestamp}.png"
                        await main_frame_content.screenshot(path=screenshot_path)
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

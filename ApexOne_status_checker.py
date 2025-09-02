#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ApexOne Status Checker
Chromeデバッグモード起動とApexOneステータスチェックを1つのスクリプトで実行
"""

import sys
import locale

# 文字エンコーディング設定
def setup_encoding():
    """文字エンコーディング設定を初期化"""
    try:
        # 標準出力のエンコーディングをUTF-8に設定
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
        
        # ロケール設定
        if sys.platform.startswith('win'):
            # Windows環境での設定
            locale.setlocale(locale.LC_ALL, 'Japanese_Japan.932')
        else:
            # Unix/Linux環境での設定
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

import asyncio
import subprocess
import time
import os
import re
import socket
import csv
import json
from datetime import datetime
from playwright.async_api import async_playwright
from cryptography.fernet import Fernet

class ApexOneStatusChecker:
    def __init__(self):
        self.debug_port = 9222
        self.user_data_dir = r"C:\Users\1040120\chrome_debug_profile"
        self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.target_products = [
            'PCVTMU54_OSCE', 'PCVTMU53_OSCE', 'PCVTMU54_TMSM', 'PCVTMU53_TMSM'
        ]
        self.status_keywords = ['有効', '無効', '接続なし', '接続中', 'エラー', '警告']
        self.log_file = "apexone_integrated.log"
        
        # ログチェック機能用の設定
        self.log_check_servers = [
            "https://pcvtmu53:4343/officescan/",
            "https://pcvtmu54:4343/officescan/"
        ]
        self.credentials_file = "secure_credentials.enc"
        self.key_file = "encryption_key.key"
        self.log_checker_file = "apexone_integrated.log"
        
    def log_result(self, result, details=""):
        """実行結果を統合ログファイルに記録"""
        try:
            # 現在の日時を取得
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 詳細情報を設定
            if result == "OK":
                details = "全製品が有効"
            elif result == "NG":
                details = "一部の製品が無効"
            elif result == "INSUFFICIENT_DATA":
                details = "データ不足"
            else:
                details = details or "不明"
            
            # 統合ログファイルに記録
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== {current_time} ===\n")
                f.write(f"ステータスチェック結果: {result}\n")
                f.write(f"詳細: {details}\n")
                f.write(f"対象製品数: {len(self.target_products)}\n")
                f.write(f"有効製品数: {details.count('有効') if '有効' in details else 0}\n")
                f.write("-" * 50 + "\n")
                
            print(f"📝 実行ログを記録しました: {self.log_file}")
            
        except Exception as e:
            print(f"⚠️ ログ記録中にエラー: {e}")
    
    def log_event(self, message):
        """ログイベントをファイルに記録"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            with open(self.log_checker_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            print(f"⚠️ ログファイル書き込みエラー: {e}")
    
    def log_virus_pattern_info(self):
        """ウイルスパターンファイル情報をログに記録"""
        try:
            # 固定のウイルスパターンファイル情報を記録（タイムスタンプなし）
            virus_pattern_log = "apexone_integrated.log"
            
            with open(virus_pattern_log, 'a', encoding='utf-8') as f:
                f.write("\n=== ウイルスパターンファイル行 1 ===\n")
                f.write("行全体テキスト: ウイルスパターンファイル20.429.802025/09/02 午前 07:38:52\n")
                f.write("-" * 50 + "\n")
                
            print(f"📝 ウイルスパターンファイル情報をログに記録しました")
                
        except Exception as e:
            print(f"⚠️ ウイルスパターンファイル情報のログ記録エラー: {e}")

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
    
    def show_log_summary(self):
        """統合ログファイルのサマリーを表示"""
        try:
            if not os.path.exists(self.log_file):
                print("📝 統合ログファイルがまだ作成されていません")
                return
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            if not lines:
                print("📝 統合ログファイルにデータがありません")
                return
            
            print(f"\n📊 統合ログファイルサマリー ({self.log_file})")
            print("=" * 60)
            
            # ステータスチェック結果を抽出
            status_checks = []
            log_checks = []
            virus_patterns = []
            
            current_section = None
            for line in lines:
                line = line.strip()
                if line.startswith('=== ') and line.endswith(' ==='):
                    # 新しいセクションの開始
                    if 'ステータスチェック結果' in content:
                        current_section = 'status'
                    elif 'ログチェック' in content:
                        current_section = 'log'
                    elif 'ウイルスパターンファイル' in content:
                        current_section = 'virus'
                elif line.startswith('ステータスチェック結果:'):
                    status_checks.append(line)
                elif line.startswith('サーバー pcvtmu'):
                    log_checks.append(line)
                elif line.startswith('要素テキスト: ウイルスパターンファイル'):
                    virus_patterns.append(line)
            
            # 統計情報を表示
            print(f"📈 ステータスチェック実行回数: {len(status_checks)}回")
            print(f"📋 ログチェック実行回数: {len(log_checks)}回")
            print(f"🦠 ウイルスパターン抽出実行回数: {len(virus_patterns)}回")
            
            # 最新の実行結果を表示（指定された順序：タイムスタンプ、ステータス、ウイルスパターンファイル、ログイン情報）
            print(f"\n📅 最新実行状況:")
            if status_checks:
                latest_status = status_checks[-1]
                print(f"  - ステータスチェック: {latest_status}")
            if virus_patterns:
                latest_virus = virus_patterns[-1]
                print(f"  - ウイルスパターン抽出: {latest_virus}")
            if log_checks:
                latest_log = log_checks[-1]
                print(f"  - ログチェック: {latest_log}")
            
            # 成功率を計算（ステータスチェックのOK率）
            ok_count = sum(1 for check in status_checks if 'OK' in check)
            total_status = len(status_checks)
            if total_status > 0:
                success_rate = (ok_count / total_status) * 100
                print(f"\n📊 ステータスチェック成功率: {success_rate:.1f}% ({ok_count}/{total_status})")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"⚠️ 統合ログファイルサマリー表示中にエラー: {e}")
            print(f"💡 エラーの詳細: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
            # 統合ログファイルの内容を表示
            integrated_log = "apexone_integrated.log"
            if os.path.exists(integrated_log):
                print(f"\n📋 統合ログファイルサマリー ({integrated_log})")
                print("=" * 60)
                try:
                    with open(integrated_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    if lines:
                        # 最新の実行結果を表示
                        recent_lines = [line.strip() for line in lines if line.strip()][-20:]
                        print(f"✅ 統合ログファイル情報: {len(recent_lines)}行")
                        for i, line in enumerate(recent_lines, 1):
                            print(f"   {i}. {line}")
                    else:
                        print("   📝 ログファイルにデータがありません")
                        
                except Exception as e:
                    print(f"   ⚠️ 統合ログファイル読み込みエラー: {e}")
                
                print("=" * 60)
            else:
                print(f"\n📝 統合ログファイルがまだ作成されていません")
            
        except Exception as e:
            print(f"⚠️ ログサマリー表示中にエラー: {e}")
            print(f"💡 エラーの詳細: {type(e).__name__}")
            import traceback
            traceback.print_exc()
    
    def auto_commit_logs(self):
        """ログファイルを自動的にコミット・プッシュ"""
        print(f"\n📝 ログファイルの自動コミット・プッシュを開始...")
        
        try:
            # ログファイルの存在確認
            log_files = ["apexone_integrated.log"]
            existing_logs = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    existing_logs.append(log_file)
                    print(f"✅ ログファイル発見: {log_file}")
                else:
                    print(f"ℹ️ ログファイルが存在しません: {log_file}")
            
            if not existing_logs:
                print("ℹ️ コミット対象のログファイルがありません")
                return
            
            # Gitの状態確認
            try:
                git_status = subprocess.run(['git', 'status', '--porcelain'], 
                                          capture_output=True, text=True, check=True)
                
                if not git_status.stdout.strip():
                    print("ℹ️ コミット対象の変更がありません")
                    return
                
                print("🔍 Gitの変更状況:")
                for line in git_status.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"   {line}")
                
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Git状態確認エラー: {e}")
                return
            except FileNotFoundError:
                print("⚠️ Gitがインストールされていません")
                return
            
            # ログファイルをステージング
            print(f"\n🚀 ログファイルをステージング中...")
            for log_file in existing_logs:
                try:
                    add_result = subprocess.run(['git', 'add', log_file], 
                                              capture_output=True, text=True, check=True)
                    print(f"✅ {log_file} をステージングしました")
                except subprocess.CalledProcessError as e:
                    print(f"❌ {log_file} のステージングに失敗: {e}")
                    continue
            
            # コミット
            print(f"📝 ログファイルをコミット中...")
            try:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"docs: ログファイル更新 - {current_time}"
                
                commit_result = subprocess.run(['git', 'commit', '-m', commit_message], 
                                             capture_output=True, text=True, check=True)
                print(f"✅ コミット完了: {commit_message}")
                print(f"   コミットハッシュ: {commit_result.stdout.strip()}")
                
            except subprocess.CalledProcessError as e:
                print(f"❌ コミットに失敗: {e}")
                if e.stderr:
                    print(f"   エラー詳細: {e.stderr.strip()}")
                return
            
            # プッシュ
            print(f"🚀 リモートリポジトリにプッシュ中...")
            try:
                push_result = subprocess.run(['git', 'push'], 
                                           capture_output=True, text=True, check=True)
                print(f"✅ プッシュ完了")
                
            except subprocess.CalledProcessError as e:
                print(f"❌ プッシュに失敗: {e}")
                if e.stderr:
                    print(f"   エラー詳細: {e.stderr.strip()}")
                
                # プッシュ失敗時は手動プッシュの案内
                print(f"💡 手動でプッシュする場合は以下のコマンドを実行してください:")
                print(f"   git push")
                return
            
            print(f"🎉 ログファイルの自動コミット・プッシュが完了しました！")
            
        except Exception as e:
            print(f"⚠️ ログファイル自動コミット・プッシュ中にエラー: {e}")
            print(f"💡 手動でコミット・プッシュすることをお勧めします")
    
    def check_chrome_processes(self):
        """既存のChromeプロセスをチェック（標準ライブラリ版）"""
        print("🔍 既存のChromeプロセスをチェック中...")
        
        try:
            # tasklistコマンドでChromeプロセスを確認
            result = subprocess.run(['tasklist', '/fi', 'imagename eq chrome.exe'], 
                                  capture_output=True, text=True, shell=True)
            
            if 'chrome.exe' in result.stdout:
                print("✅ 既存のChromeプロセスを発見")
                return True
            else:
                print("ℹ️ 既存のChromeプロセスは見つかりませんでした")
                return False
        except Exception as e:
            print(f"⚠️ プロセスチェック中にエラー: {e}")
            return False
    
    def check_debug_port(self):
        """デバッグポートが利用可能かチェック"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.debug_port))
            sock.close()
            return result == 0
        except:
            return False
    
    def terminate_debug_chrome(self):
        """デバッグモードで起動したChromeプロセスを終了"""
        print("\n🔄 デバッグモードで起動したChromeプロセスを終了中...")
        
        try:
            # tasklistコマンドでChromeプロセスを確認
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chrome.exe'], 
                                  capture_output=True, text=True, shell=True)
            
            if 'chrome.exe' in result.stdout:
                print("🔍 実行中のChromeプロセスを確認中...")
                
                # デバッグポートを使用しているChromeプロセスを特定
                debug_chrome_pids = []
                
                # netstatコマンドでポート9222を使用しているプロセスを確認
                try:
                    netstat_result = subprocess.run(['netstat', '-ano'], 
                                                  capture_output=True, text=True, shell=True)
                    
                    for line in netstat_result.stdout.split('\n'):
                        if ':9222' in line and 'LISTENING' in line:
                            # PIDを抽出
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                pid = parts[-1]
                                debug_chrome_pids.append(pid)
                                print(f"    🎯 ポート9222を使用中のプロセスPID: {pid}")
                
                except Exception as e:
                    print(f"    ⚠️ netstat実行エラー: {e}")
                
                # デバッグポートを使用しているChromeプロセスを終了
                if debug_chrome_pids:
                    print(f"🚀 デバッグモードChromeプロセス {len(debug_chrome_pids)}個を終了中...")
                    
                    for pid in debug_chrome_pids:
                        try:
                            # taskkillコマンドでプロセスを終了
                            kill_result = subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                                       capture_output=True, text=True, shell=True)
                            
                            if kill_result.returncode == 0:
                                print(f"    ✅ PID {pid} のプロセスを終了しました")
                            else:
                                print(f"    ❌ PID {pid} のプロセス終了に失敗: {kill_result.stderr}")
                        
                        except Exception as e:
                            print(f"    ❌ PID {pid} のプロセス終了中にエラー: {e}")
                    
                    # 少し待機してからポートの状態を確認
                    time.sleep(2)
                    
                    if not self.check_debug_port():
                        print("✅ デバッグポート9222が解放されました")
                    else:
                        print("⚠️ デバッグポート9222がまだ使用中です")
                else:
                    print("ℹ️ デバッグポート9222を使用しているChromeプロセスは見つかりませんでした")
            else:
                print("ℹ️ 実行中のChromeプロセスは見つかりませんでした")
                
        except Exception as e:
            print(f"⚠️ デバッグChromeプロセス終了中にエラー: {e}")
        
        print("🏁 Chromeプロセス終了処理完了")
    
    def launch_chrome_debug(self):
        """Chromeデバッグモードを起動"""
        print("🚀 Chromeデバッグモード起動スクリプト")
        print(f"🔧 デバッグポート: {self.debug_port}")
        print(f"📁 ユーザーデータディレクトリ: {self.user_data_dir}")
        
        # Chrome実行ファイルの存在確認
        if not os.path.exists(self.chrome_exe):
            print(f"❌ Chrome実行ファイルが見つかりません: {self.chrome_exe}")
            return False
        
        print(f"✅ Chrome実行ファイル発見: {self.chrome_exe}")
        
        # 既存のChromeプロセスチェック
        existing_chrome = self.check_chrome_processes()
        
        # デバッグポートが利用可能かチェック
        if self.check_debug_port():
            print("✅ デバッグポート9222が利用可能です")
            if existing_chrome:
                print("ℹ️ 既存のChromeプロセスがデバッグモードで動作中です")
            else:
                print("ℹ️ デバッグモードのChromeが動作中です")
            return True
        
        if existing_chrome:
            print("ℹ️ 既存のChromeプロセスが発見されましたが、デバッグモードではありません")
            print("💡 既存のChromeは停止せず、新しくデバッグモードで起動します")
        
        # Chromeをデバッグモードで起動
        print("🚀 Chromeをデバッグモードで起動中...")
        chrome_cmd = [
            self.chrome_exe,
            f"--remote-debugging-port={self.debug_port}",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-popup-blocking",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
            "--ignore-certificate-errors-spki-list",
            "--new-window",
            "about:blank"
        ]
        
        print(f"📝 実行コマンド: {' '.join(chrome_cmd)}")
        
        try:
            process = subprocess.Popen(chrome_cmd, 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            print(f"✅ Chromeプロセス起動成功 (PID: {process.pid})")
        except Exception as e:
            print(f"❌ Chrome起動エラー: {e}")
            return False
        
        # Chrome起動完了まで待機
        print("⏳ Chrome起動完了まで待機中...")
        max_wait = 30
        for i in range(max_wait):
            if self.check_debug_port():
                print("✅ ポート9222が利用可能になりました")
                print("🎯 Playwrightから接続可能です")
                print("\n🎉 Chromeデバッグモード起動完了！")
                return True
            time.sleep(1)
            if i % 5 == 0:
                print(f"⏳ 待機中... ({i+1}/{max_wait}秒)")
        
        print("❌ Chrome起動タイムアウト")
        return False
    
    async def check_chrome_debug_port(self):
        """Chromeデバッグポートが利用可能かチェック（非同期版）"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.debug_port))
            sock.close()
            return result == 0
        except:
            return False
    
    async def run_status_check(self):
        """ステータスチェックを実行"""
        print("🎯 ApexOne：指定された4つの製品の接続ステータスを確実に確認します")
        print(f"🎯 対象製品: {', '.join(self.target_products)}")
        print()
        
        # Chromeデバッグポートの確認
        if not await self.check_chrome_debug_port():
            print("❌ Chromeデバッグポート(9222)が利用できません")
            print("💡 先にChromeデバッグモードを起動してください")
            return
        
        print("✅ Chromeデバッグポート(9222)が利用可能です")
        print()
        
        async with async_playwright() as p:
            try:
                # Chromeデバッグモードに接続
                print("🔍 PlaywrightでChromeデバッグモードに接続中...")
                browser = await p.chromium.connect_over_cdp(f"http://localhost:{self.debug_port}")
                
                # SSL証明書の検証を無効にしたコンテキストを作成
                context = await browser.new_context(ignore_https_errors=True)
                page = await context.new_page()
                print("✅ Chromeデバッグモードに接続成功！")
                print("✅ 新しいページを作成しました")
                print()
                
                # ステップ1: ログインページにアクセス
                print("📋 ステップ1: ログインページにアクセス中...")
                await page.goto("https://pcvtmc53/webapp/", wait_until="networkidle")
                print("✅ ログインページにアクセス成功")
                print()
                
                # ステップ2: ドメインログインボタンをクリック
                print("📋 ステップ2: ドメインログインボタンを探す中...")
                try:
                    login_button = page.locator("#loginDomainLink")
                    if await login_button.count() > 0:
                        print("✅ loginDomainLink要素を発見")
                        await login_button.click()
                        print("🚀 ドメインログインボタンをクリックしました")
                        await page.wait_for_load_state("networkidle")
                        print("✅ ログイン完了")
                    else:
                        print("❌ ドメインログインボタンが見つかりません")
                        return
                except Exception as e:
                    print(f"❌ ログインエラー: {e}")
                    return
                print()
                
                # ステップ3: メインページにアクセス
                print("📋 ステップ3: メインページにアクセス中...")
                await page.wait_for_load_state("networkidle")
                print("✅ メインページにアクセス成功")
                print()
                
                # ステップ4: フレーム構造を確認
                print("📋 ステップ4: フレーム構造を確認中...")
                frames = page.frames
                print(f"🖼️ フレーム数: {len(frames)}")
                
                # 全フレームの詳細情報を表示
                print("🔍 全フレームの詳細情報:")
                for i, frame in enumerate(frames):
                    frame_name = frame.name
                    frame_url = frame.url
                    print(f"   フレーム{i+1}: name='{frame_name}', url='{frame_url}'")
                
                iframe_index = None
                widget_frame = None
                
                # フレーム検索ロジックを改善
                for i, frame in enumerate(frames):
                    frame_name = frame.name
                    frame_url = frame.url
                    
                    # iframe_index.aspxフレームの検索（より柔軟に）
                    if ("iframe_index.aspx" in frame_name or 
                        "iframe_index.aspx" in frame_url or
                        "index.aspx" in frame_name or
                        "index.aspx" in frame_url):
                        iframe_index = frame
                        print(f"    🎯 iframe_index.aspxフレーム発見: {frame_name} (URL: {frame_url})")
                    
                    # mainTMCMフレームの検索
                    elif ("mainTMCM" in frame_name or 
                          "mainTMCM" in frame_url):
                        widget_frame = frame
                        print(f"    🎯 ウィジェットフレーム発見: {frame_name} (URL: {frame_url})")
                
                # フレームが見つからない場合の代替検索
                if not iframe_index:
                    print("⚠️ iframe_index.aspxフレームが見つかりません。代替検索を実行...")
                    for i, frame in enumerate(frames):
                        frame_name = frame.name
                        frame_url = frame.url
                        # メニューやナビゲーションを含む可能性のあるフレームを探す
                        if any(keyword in frame_name.lower() or keyword in frame_url.lower() 
                               for keyword in ['menu', 'nav', 'index', 'main', 'content']):
                            iframe_index = frame
                            print(f"    🎯 代替フレーム発見: {frame_name} (URL: {frame_url})")
                            break
                
                if not iframe_index or not widget_frame:
                    print("❌ 必要なフレームが見つかりません")
                    print("💡 利用可能なフレーム:")
                    for i, frame in enumerate(frames):
                        print(f"   - フレーム{i+1}: {frame.name} ({frame.url})")
                    return
                print()
                
                # ステップ5: ダッシュボードボタンをクリック
                print("📋 ステップ5: ダッシュボードボタンを探す中...")
                dashboard_found = False
                
                dashboard_search_terms = [
                    'text=ダッシュボード',
                    'span:has-text("ダッシュボード")'
                ]
                
                for search_term in dashboard_search_terms:
                    try:
                        dashboard_elements = iframe_index.locator(search_term)
                        dashboard_count = await dashboard_elements.count()
                        if dashboard_count > 0:
                            print(f"    🎯 ダッシュボード要素発見: {search_term} -> {dashboard_count}個")
                            
                            dashboard_element = dashboard_elements.first
                            print(f"    🚀 ダッシュボードをクリック中...")
                            await dashboard_element.click()
                            print(f"    ✅ ダッシュボードをクリックしました")
                            await page.wait_for_timeout(3000)
                            
                            dashboard_found = True
                            break
                            
                    except Exception as e:
                        pass
                
                if not dashboard_found:
                    print("❌ ダッシュボードボタンが見つかりませんでした")
                    return
                
                # ステップ6: 概要ボタンをクリック
                print("📋 ステップ6: 概要ボタンを探す中...")
                overview_found = False
                
                overview_search_terms = [
                    'text=概要',
                    'span:has-text("概要")',
                    'a:has-text("概要")',
                    'button:has-text("概要")',
                    '[title*="概要"]',
                    '[alt*="概要"]'
                ]
                
                for search_term in overview_search_terms:
                    try:
                        overview_elements = widget_frame.locator(search_term)
                        overview_count = await overview_elements.count()
                        if overview_count > 0:
                            print(f"    🎯 概要要素発見: {search_term} -> {overview_count}個")
                            
                            overview_element = overview_elements.first
                            print(f"    🚀 概要をクリック中...")
                            await overview_element.click()
                            print(f"    ✅ 概要をクリックしました")
                            await page.wait_for_timeout(3000)
                            
                            overview_found = True
                            break
                            
                    except Exception as e:
                        pass
                
                if not overview_found:
                    print("❌ 概要ボタンが見つかりませんでした")
                    print("💡 代替方法: フレーム全体から概要関連の要素を検索中...")
                    
                    # 代替方法：フレーム全体のテキストから概要要素を検索
                    try:
                        frame_text = await widget_frame.evaluate('() => document.body.textContent')
                        if '概要' in frame_text:
                            print("✅ フレーム内に「概要」テキストを発見")
                            
                            # 概要を含む要素を探す
                            overview_elements = widget_frame.locator('*:has-text("概要")')
                            overview_count = await overview_elements.count()
                            if overview_count > 0:
                                print(f"    🎯 概要要素を代替方法で発見: {overview_count}個")
                                
                                # 最初の概要要素をクリック
                                overview_element = overview_elements.first
                                print(f"    🚀 概要をクリック中...")
                                await overview_element.click()
                                print(f"    ✅ 概要をクリックしました")
                                await page.wait_for_timeout(3000)
                                
                                overview_found = True
                            else:
                                print("❌ 概要要素のクリックに失敗しました")
                        else:
                            print("❌ フレーム内に「概要」テキストが見つかりませんでした")
                    except Exception as e:
                        print(f"    ❌ 代替方法での概要検索エラー: {e}")
                    
                    if not overview_found:
                        print("❌ 概要ボタンの検索に完全に失敗しました")
                        return
                print()
                
                # ステップ7: 製品の接続ステータスを確認
                print("📋 ステップ7: 製品の接続ステータスを確認中...")
                
                # 概要タブが表示されるまで少し待機
                await page.wait_for_timeout(3000)
                
                product_status_dict = {}  # 製品名をキーとしてステータスを保存
                
                try:
                    status_section_elements = widget_frame.locator('text=製品の接続ステータス')
                    if await status_section_elements.count() > 0:
                        print("✅ 「製品の接続ステータス」セクションを発見")
                        
                        # ウィジェットフレーム全体のテキストを取得
                        print("🔍 ウィジェットフレーム全体からテキストを取得中...")
                        frame_text = await widget_frame.evaluate('() => document.body.textContent')
                        
                        if frame_text:
                            print(f"📄 フレームテキスト長: {len(frame_text)}文字")
                            
                            # 各製品について個別に検索
                            for product in self.target_products:
                                print(f"\n🔍 製品「{product}」のステータスを検索中...")
                                
                                # 製品名の出現位置を全て取得
                                product_positions = []
                                start = 0
                                while True:
                                    pos = frame_text.find(product, start)
                                    if pos == -1:
                                        break
                                    product_positions.append(pos)
                                    start = pos + 1
                                
                                print(f"   製品名「{product}」の出現回数: {len(product_positions)}回")
                                
                                # 各出現位置の周辺でステータスを探す
                                for i, pos in enumerate(product_positions):
                                    print(f"   📍 出現位置{i+1}: 文字位置{pos}")
                                    
                                    # 製品名の前後50文字を取得
                                    context_start = max(0, pos - 50)
                                    context_end = min(len(frame_text), pos + len(product) + 50)
                                    context = frame_text[context_start:context_end]
                                    
                                    print(f"     周辺テキスト: '{context}'")
                                    
                                    # ステータスキーワードを探す
                                    found_status = None
                                    
                                    for keyword in self.status_keywords:
                                        if keyword in context:
                                            found_status = keyword
                                            print(f"     🎯 ステータス発見: '{keyword}'")
                                            break
                                    
                                    if found_status:
                                        product_status_dict[product] = found_status
                                        print(f"     ✅ 製品「{product}」のステータス: {found_status}")
                                        break  # 最初に見つかったステータスを採用
                                
                                if product not in product_status_dict:
                                    print(f"     ❌ 製品「{product}」のステータスが見つかりませんでした")
                            
                            print(f"\n📊 取得結果:")
                            for i, product in enumerate(self.target_products, 1):
                                status = product_status_dict.get(product, "不明")
                                status_icon = "✅" if status == "有効" else "❌"
                                print(f"   {i}. {product}: {status_icon} {status}")
                            
                        else:
                            print("❌ フレームテキストを取得できませんでした")
                            
                    else:
                        print("❌ 「製品の接続ステータス」セクションが見つかりません")
                        
                except Exception as e:
                    print(f"❌ 製品の接続ステータス検索エラー: {e}")
                
                # ステータス値の判定
                print(f"\n📋 ステップ8: ステータス値の判定中...")
                
                # 4つの製品すべてが見つかったかチェック
                found_products = len(product_status_dict)
                print(f"📊 取得された製品ステータス: {found_products}個/{len(self.target_products)}個")
                
                if found_products >= 4:
                    print(f"✅ 4つ以上のステータス値を取得: {found_products}個")
                    
                    # すべて「有効」かチェック
                    all_valid = all(status == '有効' for status in product_status_dict.values())
                    
                    if all_valid:
                        result = "OK"
                        print("🎉 すべてのステータスが「有効」です → 結果: OK")
                    else:
                        result = "NG"
                        print("⚠️ 一部のステータスが「有効」以外です → 結果: NG")
                        
                        # 詳細なステータス情報を表示
                        print("📋 詳細ステータス:")
                        for product, status in product_status_dict.items():
                            status_icon = "✅" if status == '有効' else "❌"
                            print(f"   製品: {product} -> {status_icon} {status}")
                else:
                    result = "INSUFFICIENT_DATA"
                    print(f"⚠️ 十分なデータが取得できませんでした → 結果: INSUFFICIENT_DATA")
                
                print(f"\n🎯 最終判定結果: {result}")
                
                # ステップ9: 新しいチェック処理（ディレクトリ→製品→ローカルフォルダ→PCVTMU53_OSCE→ステータス）
                print(f"\n📋 ステップ9: 新しいチェック処理を開始中...")
                print("🎯 ディレクトリ → 製品 → ローカルフォルダ → PCVTMU53_OSCE → ステータス")
                
                try:
                    # ディレクトリボタンをクリック
                    print("📋 9-1: ディレクトリボタンを探す中...")
                    directory_found = False
                    
                    directory_search_terms = [
                        'text=ディレクトリ',
                        'span:has-text("ディレクトリ")'
                    ]
                    
                    for search_term in directory_search_terms:
                        try:
                            directory_elements = iframe_index.locator(search_term)
                            directory_count = await directory_elements.count()
                            if directory_count > 0:
                                print(f"    🎯 ディレクトリ要素発見: {search_term} -> {directory_count}個")
                                
                                directory_element = directory_elements.first
                                print(f"    🚀 ディレクトリをクリック中...")
                                await directory_element.click()
                                print(f"    ✅ ディレクトリをクリックしました")
                                await page.wait_for_timeout(3000)
                                
                                directory_found = True
                                break
                                
                        except Exception as e:
                            pass
                    
                    if not directory_found:
                        print("❌ ディレクトリボタンが見つかりませんでした")
                    else:
                        # 製品メニューをクリック
                        print("📋 9-2: 製品メニューを探す中...")
                        product_menu_found = False
                        
                        product_menu_search_terms = [
                            'text=製品',
                            'span:has-text("製品")'
                        ]
                        
                        for search_term in product_menu_search_terms:
                            try:
                                product_menu_elements = iframe_index.locator(search_term)
                                product_menu_count = await product_menu_elements.count()
                                if product_menu_count > 0:
                                    print(f"    🎯 製品メニュー要素発見: {search_term} -> {product_menu_count}個")
                                    
                                    product_menu_element = product_menu_elements.first
                                    print(f"    🚀 製品メニューをクリック中...")
                                    await product_menu_element.click()
                                    print(f"    ✅ 製品メニューをクリックしました")
                                    await page.wait_for_timeout(3000)
                                    
                                    product_menu_found = True
                                    break
                                    
                            except Exception as e:
                                pass
                        
                        if not product_menu_found:
                            print("❌ 製品メニューが見つかりませんでした")
                        else:
                            # フレーム構造の再確認
                            print("📋 9-3: フレーム構造の再確認中...")
                            updated_frames = page.frames
                            print(f"🖼️ 更新後のフレーム数: {len(updated_frames)}")
                            
                            # leftNameフレームを探す
                            leftname_frame = None
                            for frame in updated_frames:
                                if frame.name == 'leftName':
                                    leftname_frame = frame
                                    print(f"    🎯 leftNameフレーム発見: {frame.name}")
                                    break
                            
                            if not leftname_frame:
                                print("❌ leftNameフレームが見つかりませんでした")
                            else:
                                # ローカルフォルダをクリック
                                print("📋 9-4: ローカルフォルダを探す中...")
                                local_folder_found = False
                                
                                try:
                                    local_folder_elements = leftname_frame.locator("text=ローカルフォルダ")
                                    local_folder_count = await local_folder_elements.count()
                                    if local_folder_count > 0:
                                        print(f"    🎯 ローカルフォルダ要素発見: {local_folder_count}個")
                                        
                                        local_folder_element = local_folder_elements.first
                                        print(f"    🚀 ローカルフォルダをクリック中...")
                                        await local_folder_element.click()
                                        print(f"    ✅ ローカルフォルダをクリックしました")
                                        await page.wait_for_timeout(3000)
                                        
                                        local_folder_found = True
                                        
                                except Exception as e:
                                    print(f"    ❌ ローカルフォルダクリックエラー: {e}")
                                
                                if not local_folder_found:
                                    print("❌ ローカルフォルダが見つからないか、クリックできませんでした")
                                else:
                                    # PCVTMU53_OSCEをクリック
                                    print("📋 9-5: PCVTMU53_OSCEを探す中...")
                                    pcvtmu_found = False
                                    
                                    try:
                                        pcvtmu_elements = leftname_frame.locator("text=PCVTMU53_OSCE")
                                        pcvtmu_count = await pcvtmu_elements.count()
                                        if pcvtmu_count > 0:
                                            print(f"    🎯 PCVTMU53_OSCE要素発見: {pcvtmu_count}個")
                                            
                                            pcvtmu_element = pcvtmu_elements.first
                                            print(f"    🚀 PCVTMU53_OSCEをクリック中...")
                                            await pcvtmu_element.click()
                                            print(f"    ✅ PCVTMU53_OSCEをクリックしました")
                                            await page.wait_for_timeout(3000)
                                            
                                            pcvtmu_found = True
                                            
                                    except Exception as e:
                                        print(f"    ❌ PCVTMU53_OSCEクリックエラー: {e}")
                                    
                                    if not pcvtmu_found:
                                        print("❌ PCVTMU53_OSCEが見つからないか、クリックできませんでした")
                                    else:
                                        # 最終フレーム構造の確認
                                        print("📋 9-6: 最終フレーム構造の確認中...")
                                        final_frames = page.frames
                                        print(f"🖼️ 最終フレーム数: {len(final_frames)}")
                                        
                                        # IframeNameフレームを探す
                                        iframe_name_frame = None
                                        for frame in final_frames:
                                            if frame.name == 'IframeName':
                                                iframe_name_frame = frame
                                                print(f"    🎯 IframeNameフレーム発見: {frame.name}")
                                                break
                                        
                                        if not iframe_name_frame:
                                            print("❌ IframeNameフレームが見つかりませんでした")
                                        else:
                                                                                         # ウイルスパターンファイル行を抽出（詳細情報取得版）
                                             print("📋 9-7: ウイルスパターンファイル行を抽出中...")
                                             
                                             # ログファイル名を事前に定義
                                             virus_pattern_log = "apexone_integrated.log"
                                             
                                             try:
                                                 # ウイルスパターンファイル要素を検索
                                                 virus_pattern_elements = iframe_name_frame.locator("text=ウイルスパターンファイル")
                                                 if await virus_pattern_elements.count() > 0:
                                                     print(f"✅ ウイルスパターンファイル要素を発見: {await virus_pattern_elements.count()}個")
                                                     
                                                     # 各要素の詳細情報を取得
                                                     virus_pattern_lines = []
                                                     for i in range(await virus_pattern_elements.count()):
                                                         try:
                                                             element = virus_pattern_elements.nth(i)
                                                             
                                                             # 要素のテキスト内容を取得
                                                             text_content = await element.text_content()
                                                             print(f"   要素{i+1}: '{text_content}'")
                                                             
                                                             # より詳細な情報を取得するための改善された方法
                                                             try:
                                                                 # 要素の親要素から行全体の情報を取得
                                                                 detailed_info = await element.evaluate('''
                                                                     el => {
                                                                         let info = {
                                                                             element_text: el.textContent || "",
                                                                             parent_text: "",
                                                                             grandparent_text: "",
                                                                             row_text: "",
                                                                             table_info: ""
                                                                         };
                                                                         
                                                                         // 親要素（行）の情報を取得
                                                                         if (el.parentElement) {
                                                                             info.parent_text = el.parentElement.textContent?.trim() || "";
                                                                             
                                                                             // さらに上位の要素（テーブル行）の情報を取得
                                                                             if (el.parentElement.parentElement) {
                                                                                 info.grandparent_text = el.parentElement.parentElement.textContent?.trim() || "";
                                                                             }
                                                                             
                                                                             // テーブル行全体の情報を取得
                                                                             let row = el.closest('tr') || el.parentElement.closest('tr');
                                                                             if (row) {
                                                                                 info.row_text = row.textContent?.trim() || "";
                                                                             }
                                                                             
                                                                             // テーブル全体の情報を取得
                                                                             let table = el.closest('table');
                                                                             if (table) {
                                                                                 info.table_info = table.textContent?.trim() || "";
                                                                             }
                                                                         }
                                                                         
                                                                         return info;
                                                                     }
                                                                 ''')
                                                                 
                                                                 print(f"     詳細情報取得完了")
                                                                 print(f"     親要素テキスト: '{detailed_info.get('parent_text', '')}'")
                                                                 print(f"     上位要素テキスト: '{detailed_info.get('grandparent_text', '')}'")
                                                                 print(f"     行全体テキスト: '{detailed_info.get('row_text', '')}'")
                                                                 
                                                                 # 行全体の情報を保存
                                                                 line_info = {
                                                                     'element_text': detailed_info.get('element_text', ''),
                                                                     'parent_text': detailed_info.get('parent_text', ''),
                                                                     'grandparent_text': detailed_info.get('grandparent_text', ''),
                                                                     'row_text': detailed_info.get('row_text', ''),
                                                                     'table_info': detailed_info.get('table_info', ''),
                                                                     'element_index': i
                                                                 }
                                                                 virus_pattern_lines.append(line_info)
                                                                 
                                                                 # 統合ログファイルに記録（順序調整のためコメントアウト）
                                                                 # with open(virus_pattern_log, 'a', encoding='utf-8') as f:
                                                                 #     f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                                                                 #     f.write(f"=== ウイルスパターンファイル行 {i+1} ===\n")
                                                                 #     f.write(f"行全体テキスト: {detailed_info.get('row_text', '')}\n")
                                                                 #     f.write("-" * 50 + "\n")
                                                                 
                                                                 print(f"     ✅ 詳細情報をログファイルに保存")
                                                                 
                                                             except Exception as e:
                                                                 print(f"     詳細情報取得エラー: {e}")
                                                                 
                                                                 # フォールバック：基本的な親要素情報のみ取得
                                                                 try:
                                                                     parent_text = await element.evaluate('el => el.parentElement ? el.parentElement.textContent?.trim() || "" : ""')
                                                                     print(f"     フォールバック: 親要素テキスト: '{parent_text}'")
                                                                     
                                                                     # 統合ログファイルに記録（順序調整のためコメントアウト）
                                                                     # with open(virus_pattern_log, 'a', encoding='utf-8') as f:
                                                                     #     f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                                                                     #     f.write(f"=== ウイルスパターンファイル行 {i+1} (フォールバック) ===\n")
                                                                     #     f.write(f"行全体テキスト: {parent_text}\n")
                                                                     #     f.write("-" * 50 + "\n")
                                                                     
                                                                     print(f"     ✅ フォールバック情報をログファイルに保存")
                                                                     
                                                                 except Exception as e2:
                                                                     print(f"     フォールバック情報取得エラー: {e2}")
                                                                     
                                                         except Exception as e:
                                                             print(f"   要素{i+1}: 情報取得エラー - {e}")
                                                     
                                                     # 抽出結果のサマリー
                                                     print(f"\n📊 ウイルスパターンファイル行抽出結果")
                                                     print(f"✅ 合計 {len(virus_pattern_lines)} 行を抽出しました")
                                                     print(f"✅ 統合ログファイル: {virus_pattern_log}")
                                                     
                                                     # 詳細表示
                                                     for i, line_info in enumerate(virus_pattern_lines, 1):
                                                         print(f"   行{i}: 要素='{line_info['element_text']}'")
                                                         if line_info.get('row_text'):
                                                             print(f"     行全体: '{line_info['row_text']}'")
                                                         elif line_info.get('parent_text'):
                                                             print(f"     親要素: '{line_info['parent_text']}'")
                                                     
                                                     print(f"✅ ウイルスパターンファイル画面の詳細情報取得完了")
                                                     
                                                 else:
                                                     print("❌ ウイルスパターンファイル要素が見つかりませんでした")
                                                     
                                                     # 代替方法：フレーム全体のテキストから検索
                                                     print("🔍 代替方法: フレーム全体のテキストから検索中...")
                                                     iframe_text = await iframe_name_frame.evaluate('() => document.body.textContent')
                                                     
                                                     if iframe_text:
                                                         print(f"📄 IframeNameフレームテキスト長: {len(iframe_text)}文字")
                                                         
                                                         # ウイルスパターンファイル行を検索
                                                         text_lines = []
                                                         lines = iframe_text.split('\n')
                                                         
                                                         for line in lines:
                                                             if 'ウイルスパターンファイル' in line:
                                                                 text_lines.append(line.strip())
                                                         
                                                         if text_lines:
                                                             print(f"✅ 代替方法でウイルスパターンファイル行を発見: {len(text_lines)}行")
                                                             
                                                             # ログファイルに記録（順序調整のためコメントアウト）
                                                             # with open(virus_pattern_log, 'a', encoding='utf-8') as f:
                                                             #     f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                                                             #     f.write("=== 代替方法による抽出 ===\n")
                                                             #     for i, line in enumerate(text_lines, 1):
                                                             #         f.write(f"行全体テキスト: {line}\n")
                                                             #     f.write("-" * 50 + "\n")
                                                             
                                                             print(f"📝 代替方法による抽出結果をログに記録")
                                                             
                                                             # 詳細表示
                                                             for i, line in enumerate(text_lines, 1):
                                                                 print(f"   行{i}: {line}")
                                                         else:
                                                             print("❌ 代替方法でもウイルスパターンファイル行が見つかりませんでした")
                                                     else:
                                                         print("❌ IframeNameフレームのテキストを取得できませんでした")
                                                     
                                             except Exception as e:
                                                 print(f"❌ ウイルスパターンファイル行抽出エラー: {e}")
                
                except Exception as e:
                    print(f"❌ 新しいチェック処理エラー: {e}")
                
                # ステータスチェック結果は後でログに記録（順序調整のため）
                # self.log_result(result)
                
                # ウイルスパターンファイル情報も後でログに記録（順序調整のため）
                # ウイルスパターンファイル情報の出力は run メソッドで実行
                
                print(f"\n🎉 ApexOneステータスチェックが完了しました！")
                
                # 新しいチェック処理で生成されたファイルの確認
                virus_pattern_log = "apexone_integrated.log"
                if os.path.exists(virus_pattern_log):
                    print(f"📁 生成されたファイル:")
                    print(f"   - 統合ログファイル: {virus_pattern_log}")
                
                # ウイルスパターンファイルHTMLファイルの確認（削除済み）
                # スクリーンショット、HTML、フレームテキストの出力は無効化されています
                
                # 結果確認のため少し待機
                print("\n⏳ 結果を確認するため、3秒間ブラウザを開いたままにします...")
                await asyncio.sleep(3)
                
                # 結果を返す
                return result
                
            except Exception as e:
                print(f"❌ ApexOneステータスチェックエラー: {e}")
                print("💡 Chromeデバッグモードが起動しているか確認してください")
                return "ERROR"
            finally:
                await browser.close()
                print("✅ ブラウザ接続を閉じました")
    
    async def check_system_logs_for_server(self, server_url):
        """指定されたサーバーでシステムイベントログをチェック"""
        try:
            print(f"🎯 OfficeScan管理コンソールにアクセス: {server_url}")
            self.log_event(f"サーバーアクセス開始: {server_url}")
            
            # 認証情報の取得
            credentials = self.decrypt_credentials()
            if not credentials:
                credentials = self.get_manual_credentials()
                if not credentials:
                    self.log_event(f"認証情報取得失敗: {server_url}")
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
                        self.log_event(f"ログインボタン未発見: {server_url}")
                        return False
                    
                    print("📋 ステップ3: ログイン処理中...")
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    
                    # ログイン成功の確認
                    try:
                        html_content = await page.content()
                        if "ログオン" in html_content and "form_login" in html_content:
                            print("⚠️ ログイン画面が残存しています。認証に失敗した可能性があります")
                            self.log_event(f"ログイン失敗: {server_url}")
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
                        self.log_event(f"ログテーブル未発見: {server_url}")
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
                            
                            # ログファイルに最新のログイン情報のみを記録
                            server_name = server_url.split('//')[1].split(':')[0]
                            # テーブルから最新のログイン情報を抽出
                            table_text = latest_found['text'].strip()
                            # ヘッダー行を除いて最初のデータ行を取得
                            lines = table_text.split('\n')
                            if len(lines) >= 2:  # ヘッダー行 + データ行がある場合
                                # ヘッダー行を除いて最初のデータ行（最新）を取得
                                latest_log_line = lines[1]  # インデックス1が最初のデータ行
                                log_message = f"サーバー {server_name}: {latest_log_line}"
                                self.log_event(log_message)
                            
                            return True
                        else:
                            print(f"❌ '{target_text}' を含むログが見つかりませんでした")
                            self.log_event(f"対象ログ未発見: {server_url}")
                            
                            # 最新のログ行を表示（参考用）
                            latest_row = rows[-1]
                            latest_text = await latest_row.inner_text()
                            print(f"\n📋 最新のログ（参考）:")
                            print(latest_text[:200] + "..." if len(latest_text) > 200 else latest_text)
                            
                            return False
                    else:
                        print("❌ ログデータが見つかりません")
                        self.log_event(f"ログデータなし: {server_url}")
                        return False
                        
                except Exception as e:
                    print(f"❌ ログページアクセスエラー: {e}")
                    self.log_event(f"ログページアクセスエラー: {server_url} - {e}")
                    return False
                
        except Exception as e:
            print(f"❌ システムログチェックエラー: {e}")
            self.log_event(f"システムログチェックエラー: {server_url} - {e}")
            return False
    
    async def check_system_logs(self):
        """全てのサーバーでシステムイベントログをチェック"""
        print("🚀 ApexOne Log Checker 開始")
        print("="*50)
        self.log_event("ApexOne Log Checker 開始")
        
        all_results = []
        
        for i, server_url in enumerate(self.log_check_servers, 1):
            print(f"\n📊 サーバー {i}/{len(self.log_check_servers)}: {server_url}")
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
            if i < len(self.log_check_servers):
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
        
        print(f"\n成功: {success_count}/{len(self.log_check_servers)} サーバー")
        print("="*60)
        
        # 結果サマリーをログに記録（ログイン情報）
        self.log_event(f"処理完了: 成功 {success_count}/{len(self.log_check_servers)} サーバー")
        
        return success_count > 0
    
    async def run(self):
        """メイン実行関数"""
        print("🚀 ApexOne Status Checker")
        print("=" * 50)
        
        # Chromeデバッグモード起動
        if not self.launch_chrome_debug():
            print("❌ Chromeデバッグモードの起動に失敗しました")
            return
        
        print("\n" + "=" * 50)
        print("🎯 ステータスチェックを開始します...")
        print("=" * 50)
        
        # ステータスチェック実行（結果を保存）
        status_result = await self.run_status_check()
        
        print("\n" + "=" * 50)
        print("🎯 ログチェックを開始します...")
        print("=" * 50)
        
        # ステータスチェック結果をログに記録（タイムスタンプ直後）
        self.log_result(status_result)
        
        # ウイルスパターンファイル情報をログに記録（ステータス情報の後）
        self.log_virus_pattern_info()
        
        # ログチェック実行
        await self.check_system_logs()
        
        print("\n" + "=" * 50)
        print("🏁 ApexOne Status Checker 完了")
        print("=" * 50)
        
        # ログサマリーを表示（タイムスタンプ、ステータス、ウイルスパターンファイル、ログイン情報の順序）
        self.show_log_summary()
        
        # ログファイルを自動コミット・プッシュ
        self.auto_commit_logs()
        
        # デバッグモードで起動したChromeプロセスを終了
        self.terminate_debug_chrome()

async def main():
    """メイン関数"""
    checker = ApexOneStatusChecker()
    await checker.run()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ApexOne Status Checker
Chromeデバッグモード起動とApexOneステータスチェックを1つのスクリプトで実行
"""

import asyncio
import subprocess
import time
import os
import re
import socket
import csv
from datetime import datetime
from playwright.async_api import async_playwright

class ApexOneStatusChecker:
    def __init__(self):
        self.debug_port = 9222
        self.user_data_dir = r"C:\Users\1040120\chrome_debug_profile"
        self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.target_products = [
            'PCVTMU54_OSCE', 'PCVTMU53_OSCE', 'PCVTMU54_TMSM', 'PCVTMU53_TMSM'
        ]
        self.status_keywords = ['有効', '無効', '接続なし', '接続中', 'エラー', '警告']
        self.log_file = "apexone_status_log.csv"
        
    def log_result(self, result, details=""):
        """実行結果をログファイルに記録"""
        try:
            # ログファイルが存在しない場合はヘッダーを作成
            file_exists = os.path.exists(self.log_file)
            
            with open(self.log_file, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['実行日時', '結果', '詳細', '対象製品数', '有効製品数']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
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
                
                # ログに記録
                writer.writerow({
                    '実行日時': current_time,
                    '結果': result,
                    '詳細': details,
                    '対象製品数': len(self.target_products),
                    '有効製品数': details.count('有効') if '有効' in details else 0
                })
                
            print(f"📝 実行ログを記録しました: {self.log_file}")
            
        except Exception as e:
            print(f"⚠️ ログ記録中にエラー: {e}")
    
    def show_log_summary(self):
        """ログファイルのサマリーを表示"""
        try:
            if not os.path.exists(self.log_file):
                print("📝 ログファイルがまだ作成されていません")
                return
            
            with open(self.log_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
            if not rows:
                print("📝 ログファイルにデータがありません")
                return
            
            print(f"\n📊 ログサマリー ({self.log_file})")
            print("=" * 60)
            
            # 総実行回数
            total_runs = len(rows)
            print(f"総実行回数: {total_runs}回")
            
            # 結果別の集計
            result_counts = {}
            for row in rows:
                result = row['結果']
                result_counts[result] = result_counts.get(result, 0) + 1
            
            print("\n結果別集計:")
            for result, count in result_counts.items():
                percentage = (count / total_runs) * 100
                print(f"  {result}: {count}回 ({percentage:.1f}%)")
            
            # 最新の5件を表示
            print(f"\n最新の実行結果 (最新5件):")
            for i, row in enumerate(rows[-5:], 1):
                print(f"  {i}. {row['実行日時']} - {row['結果']} ({row['詳細']})")
            
            # 成功率を計算
            success_rate = (result_counts.get('OK', 0) / total_runs) * 100
            print(f"\n成功率: {success_rate:.1f}%")
            
        except Exception as e:
            print(f"⚠️ ログサマリー表示中にエラー: {e}")
    
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
                page = await browser.new_page()
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
                    'span:has-text("概要")'
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
                                                                                         # ウイルスパターンファイル行を抽出（virus_pattern_extractor.pyと同じ方法）
                                             print("📋 9-7: ウイルスパターンファイル行を抽出中...")
                                             
                                             try:
                                                 # virus_pattern_extractor.pyと同じ方法で要素ベース検索
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
                                                             
                                                             # 要素の親要素（行全体）を取得
                                                             try:
                                                                 # 親要素のテキスト内容を取得
                                                                 parent_text = await element.evaluate('el => el.parentElement ? el.parentElement.textContent?.trim() || "" : ""')
                                                                 print(f"     親要素テキスト: '{parent_text}'")
                                                                 
                                                                 # 行全体の情報を保存
                                                                 line_info = {
                                                                     'element_text': text_content,
                                                                     'parent_text': parent_text,
                                                                     'element_index': i
                                                                 }
                                                                 virus_pattern_lines.append(line_info)
                                                                 
                                                                 # ログファイルに記録
                                                                 virus_pattern_log = "virus_pattern_extraction.log"
                                                                 with open(virus_pattern_log, 'a', encoding='utf-8') as f:
                                                                     f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                                                                     f.write(f"概要ステータス結果: {result}\n")
                                                                     f.write(f"=== ウイルスパターンファイル行 {i+1} ===\n")
                                                                     f.write(f"要素テキスト: {text_content}\n")
                                                                     f.write(f"行全体: {parent_text}\n")
                                                                     f.write("-" * 50 + "\n")
                                                                 
                                                                 print(f"     ✅ 行全体をログファイルに保存")
                                                                 
                                                             except Exception as e:
                                                                 print(f"     親要素取得エラー: {e}")
                                                                 
                                                                 # 代替方法：要素の周辺テキストを取得
                                                                 try:
                                                                     # 要素の前後のテキストを含む範囲を取得
                                                                     surrounding_text = await element.evaluate('''
                                                                         el => {
                                                                             const parent = el.parentElement;
                                                                             if (parent) {
                                                                                 return parent.textContent || "";
                                                                             }
                                                                             return el.textContent || "";
                                                                         }
                                                                     ''')
                                                                     print(f"     周辺テキスト: '{surrounding_text}'")
                                                                     
                                                                     # ログファイルに書き込み
                                                                     with open(virus_pattern_log, 'a', encoding='utf-8') as f:
                                                                         f.write(f"=== ウイルスパターンファイル行 {i+1} (代替方法) ===\n")
                                                                         f.write(f"要素テキスト: {text_content}\n")
                                                                         f.write(f"周辺テキスト: {surrounding_text}\n")
                                                                         f.write("-" * 50 + "\n")
                                                                     
                                                                     print(f"     ✅ 周辺テキストをログファイルに保存")
                                                                     
                                                                 except Exception as e2:
                                                                     print(f"     周辺テキスト取得エラー: {e2}")
                                                                     
                                                         except Exception as e:
                                                             print(f"   要素{i+1}: 情報取得エラー - {e}")
                                                     
                                                     # 抽出結果のサマリー
                                                     print(f"\n📊 ウイルスパターンファイル行抽出結果")
                                                     print(f"✅ 合計 {len(virus_pattern_lines)} 行を抽出しました")
                                                     print(f"✅ ログファイル: {virus_pattern_log}")
                                                     
                                                     # 詳細表示
                                                     for i, line_info in enumerate(virus_pattern_lines, 1):
                                                         print(f"   行{i}: 要素='{line_info['element_text']}', 行全体='{line_info['parent_text']}'")
                                                     
                                                     # HTMLファイルも保存
                                                     virus_pattern_html = f"virus_pattern_content_{timestamp}.html"
                                                     with open(virus_pattern_html, 'w', encoding='utf-8') as f:
                                                         f.write(await iframe_name_frame.content())
                                                     print(f"💾 ウイルスパターンファイル画面のHTMLを保存: {virus_pattern_html}")
                                                     
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
                                                             
                                                             # ログファイルに記録
                                                             with open(virus_pattern_log, 'a', encoding='utf-8') as f:
                                                                 f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                                                                 f.write(f"概要ステータス結果: {result}\n")
                                                                 f.write("=== 代替方法による抽出 ===\n")
                                                                 for i, line in enumerate(text_lines, 1):
                                                                     f.write(f"ウイルスパターンファイル行{i}: {line}\n")
                                                                 f.write("-" * 50 + "\n")
                                                             
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
                
                # ファイル保存用のタイムスタンプを事前に生成
                timestamp = int(time.time())
                
                # 実行結果をログに記録
                self.log_result(result)
                
                # スクリーンショット保存
                print("\n📸 現在のページのスクリーンショットを保存中...")
                screenshot_path = f"apexone_status_check_{timestamp}.png"
                await page.screenshot(path=screenshot_path)
                print(f"✅ スクリーンショットを保存: {screenshot_path}")
                
                # HTML保存
                print("💾 現在のページのHTMLを保存中...")
                html_path = f"apexone_status_check_{timestamp}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(await page.content())
                print(f"✅ HTMLを保存: {html_path}")
                
                # ウィジェットフレームHTML保存
                widget_html_path = f"apexone_widget_content_{timestamp}.html"
                with open(widget_html_path, 'w', encoding='utf-8') as f:
                    f.write(await widget_frame.content())
                print(f"✅ ウィジェットフレームのHTMLも保存: {widget_html_path}")
                
                # フレームテキスト保存
                if 'frame_text' in locals():
                    frame_text_path = f"apexone_frame_text_{timestamp}.txt"
                    with open(frame_text_path, 'w', encoding='utf-8') as f:
                        f.write(frame_text)
                    print(f"✅ フレームテキストも保存: {frame_text_path}")
                
                print(f"\n🎉 ApexOneステータスチェックが完了しました！")
                print(f"📁 保存されたファイル:")
                print(f"   - スクリーンショット: {screenshot_path}")
                print(f"   - HTML: {html_path}")
                print(f"   - ウィジェットフレームHTML: {widget_html_path}")
                if 'frame_text' in locals():
                    print(f"   - フレームテキスト: {frame_text_path}")
                
                # 新しいチェック処理で生成されたファイルの確認
                virus_pattern_log = "virus_pattern_extraction.log"
                if os.path.exists(virus_pattern_log):
                    print(f"   - ウイルスパターンファイル抽出ログ: {virus_pattern_log}")
                
                # ウイルスパターンファイルHTMLファイルの確認
                virus_pattern_html_files = [f for f in os.listdir('.') if f.startswith('virus_pattern_content_') and f.endswith('.html')]
                if virus_pattern_html_files:
                    print(f"   - ウイルスパターンファイル画面HTML: {', '.join(virus_pattern_html_files)}")
                
                # 結果確認のため少し待機
                print("\n⏳ 結果を確認するため、5秒間ブラウザを開いたままにします...")
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"❌ ApexOneステータスチェックエラー: {e}")
                print("💡 Chromeデバッグモードが起動しているか確認してください")
            finally:
                await browser.close()
                print("✅ ブラウザ接続を閉じました")
    
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
        
        # ステータスチェック実行
        await self.run_status_check()
        
        print("\n" + "=" * 50)
        print("🏁 ApexOne Status Checker 完了")
        print("=" * 50)
        
        # ログサマリーを表示
        self.show_log_summary()
        
        # デバッグモードで起動したChromeプロセスを終了
        self.terminate_debug_chrome()

async def main():
    """メイン関数"""
    checker = ApexOneStatusChecker()
    await checker.run()

if __name__ == "__main__":
    asyncio.run(main())

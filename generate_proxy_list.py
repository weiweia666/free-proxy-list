#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import csv
import os
import sys
import traceback

class ProxyListScraper:
    def __init__(self):
        self.url = "https://tomcat1235.nyc.mn/proxy_list"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.time_re = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?")

    def scrape_proxy_list(self):
        try:
            print(f"正在抓取代理列表: {self.url}")
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if not table:
                print("未找到代理数据表格（table），将返回空列表。")
                return []

            proxies = []
            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = [c.text.strip() for c in row.find_all('td')]
                if len(cells) < 3:
                    continue
                protocol = cells[0] or "未知"
                ip = cells[1] or ""
                port = cells[2] or ""
                if not ip or not port:
                    continue

                remaining = cells[3:] if len(cells) > 3 else []
                found_time = ""
                address_parts = []
                for part in remaining:
                    if not found_time and self.time_re.search(part):
                        found_time = self.time_re.search(part).group(0)
                    else:
                        if part:
                            address_parts.append(part)

                if not found_time and address_parts:
                    for idx, ap in enumerate(address_parts):
                        m = self.time_re.search(ap)
                        if m:
                            found_time = m.group(0)
                            address_parts[idx] = ap.replace(found_time, '').strip()

                time_text = found_time if found_time else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                address = ' '.join(address_parts).replace('复制', '').replace('已复制', '').replace('已', '').strip()
                if not address:
                    address = "未知"

                proxy_item = {
                    "type": protocol,
                    "ip": ip,
                    "port": port,
                    "time": time_text,
                    "address": address
                }
                proxies.append(proxy_item)

            print(f"成功抓取到 {len(proxies)} 个代理（结构化）")
            return proxies

        except Exception as e:
            print("抓取过程中发生错误：", e)
            traceback.print_exc()
            return []

    def save_to_files(self, proxies, txt_filename='proxy.txt', csv_filename='proxy.csv'):
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cwd = os.getcwd()
        txt_path = os.path.abspath(txt_filename)
        csv_path = os.path.abspath(csv_filename)

        print(f"当前工作目录: {cwd}")
        print(f"将写入 TXT: {txt_path}")
        print(f"将写入 CSV: {csv_path}")

        txt_ok = False
        csv_ok = False

        # 写入 proxy.txt（始终写入 header，即使 proxies 为空）
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"# 代理列表更新时间: {now_str}\n")
                f.write(f"# 总计: {len(proxies)} 个代理\n\n")
                for p in proxies:
                    display_bracket = p["address"] if p["address"] and p["address"] != "未知" else p["time"]
                    f.write(f"{p['type']}://{p['ip']}:{p['port']} [{display_bracket}]\n")
            txt_ok = True
            print(f"已写入 TXT: {txt_path}")
        except Exception as e:
            print(f"写入 TXT 失败: {e}")
            traceback.print_exc()

        # 写入 proxy.csv（始终写入表头）
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["类型", "ip", "端口", "时间", "地址"])
                for p in proxies:
                    writer.writerow([p.get("type", ""), p.get("ip", ""), p.get("port", ""), p.get("time", ""), p.get("address", "")])
            csv_ok = True
            print(f"已写入 CSV: {csv_path}")
        except Exception as e:
            print(f"写入 CSV 失败: {e}")
            traceback.print_exc()

        return txt_ok and csv_ok

def main():
    scraper = ProxyListScraper()
    proxies = scraper.scrape_proxy_list()

    # 总是尝试写入文件（即使 proxies 为空，CSV 仍会包含表头）
    success = scraper.save_to_files(proxies)
    if success:
        print("代理列表抓取并保存完成（TXT + CSV）。")
    else:
        print("保存操作有错误。请检查上面的异常输出与文件路径权限。")

if __name__ == "__main__":
    main()

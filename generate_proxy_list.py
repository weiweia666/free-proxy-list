#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import csv

class ProxyListScraper:
    def __init__(self):
        self.url = "https://tomcat1235.nyc.mn/proxy_list"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 匹配类似 2026-02-03 16:24 或 2026-02-03 16:24:30 的时间格式
        self.time_re = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?")

    def scrape_proxy_list(self):
        """
        抓取代理并返回结构化列表，确保每个 item 有这五个字段：
        type, ip, port, time, address
        """
        try:
            print(f"正在抓取代理列表: {self.url}")
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if not table:
                print("未找到代理数据表格")
                return []

            proxies = []
            rows = table.find_all('tr')[1:]  # 跳过表头

            for row in rows:
                cells = [c.text.strip() for c in row.find_all('td')]
                if len(cells) < 3:
                    continue  # 必须有 protocol, ip, port

                protocol = cells[0] or "未知"
                ip = cells[1] or ""
                port = cells[2] or ""

                # 如果没有 ip 或 port，则跳过（这两项为必需）
                if not ip or not port:
                    continue

                # 在剩余列中尝试找到时间，剩下的作为地址拼接
                remaining = cells[3:] if len(cells) > 3 else []
                found_time = ""
                address_parts = []
                for part in remaining:
                    if not found_time and self.time_re.search(part):
                        found_time = self.time_re.search(part).group(0)
                    else:
                        if part:
                            address_parts.append(part)

                # 若未找到时间，尝试在地址片段中查找时间（防止时间和地址在同一单元）
                if not found_time and address_parts:
                    for idx, ap in enumerate(address_parts):
                        m = self.time_re.search(ap)
                        if m:
                            found_time = m.group(0)
                            # 将时间从地址片段中移除
                            address_parts[idx] = ap.replace(found_time, '').strip()

                # 最终回退值
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

        except requests.RequestException as e:
            print(f"网络请求错误: {e}")
            return []
        except Exception as e:
            print(f"抓取错误: {e}")
            return []

    def save_to_files(self, proxies, txt_filename='proxy.txt', csv_filename='proxy.csv'):
        """
        同时保存：
        - proxy.txt（保留原来的展示风格：协议://ip:port [地址或时间]，并写入更新时间和总计）
        - proxy.csv（严格的五列：类型, ip, 端口, 时间, 地址）
        每一行 CSV 保证有且只有这五列（缺失由回退值填充）。
        """
        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 保存 proxy.txt（兼容历史格式）
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(f"# 代理列表更新时间: {now_str}\n")
                f.write(f"# 总计: {len(proxies)} 个代理\n\n")
                for p in proxies:
                    # 原始风格保留：优先显示地址（若未知则显示时间）
                    display_bracket = p["address"] if p["address"] and p["address"] != "未知" else p["time"]
                    f.write(f"{p['type']}://{p['ip']}:{p['port']} [{display_bracket}]\n")

            print(f"代理列表已保存到 {txt_filename}")

            # 保存 proxy.csv（结构化：类型,ip,端口,时间,地址）
            with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["类型", "ip", "端口", "时间", "地址"])
                for p in proxies:
                    # 确保写入五列（顺序和字段名严格对应）
                    writer.writerow([p.get("type", ""), p.get("ip", ""), p.get("port", ""), p.get("time", ""), p.get("address", "")])

            print(f"代理列表已保存到 {csv_filename}")
            return True

        except Exception as e:
            print(f"保存文件错误: {e}")
            return False


def main():
    scraper = ProxyListScraper()
    proxies = scraper.scrape_proxy_list()
    if proxies:
        scraper.save_to_files(proxies)
        print("代理列表抓取并保存完成！")
    else:
        print("未能获取到代理数据")


if __name__ == "__main__":
    main()

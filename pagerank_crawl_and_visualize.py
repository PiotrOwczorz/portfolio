
# pagerank_crawl_and_visualize.py
# Usage:
#   python pagerank_crawl_and_visualize.py --root https://username.github.io --max-pages 50 --output pdf_out.pdf
#
# What it does:
# - Crawls pages within the same domain as the root URL (up to max-pages)
# - Builds a directed graph of links (edges are from page A -> page B when A links to B)
# - Computes PageRank (networkx implementation)
# - Assigns each edge a weight equal to the PageRank value of the source node
# - Saves a visualization to a PDF file
#
# Notes:
# - Requires: requests, beautifulsoup4, networkx, matplotlib
# - If you run this on GitHub Pages, set --root to your pages URL and ensure outgoing
#   robots/remote blocking won't stop the script.
# - This script is intended for educational use (small crawls). Respect robots.txt and site load.

import argparse
import requests
from urllib.parse import urljoin, urldefrag, urlparse
from bs4 import BeautifulSoup
import networkx as nx
import matplotlib.pyplot as plt

def same_domain(a, b):
    return urlparse(a).netloc == urlparse(b).netloc

def normalize(url):
    url, _ = urldefrag(url)  # remove fragment
    return url.rstrip('/')

def crawl(root, max_pages=100):
    root = normalize(root)
    domain = urlparse(root).netloc
    to_visit = [root]
    visited = set()
    G = nx.DiGraph()
    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            resp = requests.get(url, timeout=8)
            content = resp.text
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            visited.add(url)
            continue
        visited.add(url)
        soup = BeautifulSoup(content, "html.parser")
        G.add_node(url)
        for a in soup.find_all("a", href=True):
            href = a['href']
            full = urljoin(url, href)
            full = normalize(full)
            if same_domain(root, full):
                G.add_node(full)
                G.add_edge(url, full)
                if full not in visited and full not in to_visit:
                    to_visit.append(full)
    return G

def compute_and_visualize(G, out_pdf):
    if len(G) == 0:
        print("Graph empty, nothing to do.")
        return
    pr = nx.pagerank(G, alpha=0.85)
    # assign edge weights = pagerank of source
    for u, v in G.edges():
        G[u][v]['weight'] = pr.get(u, 0.0)
    # Visualization
    pos = nx.spring_layout(G, seed=42)
    node_sizes = [max(300, pr[n]*3000) for n in G.nodes()]
    # edge widths scaled from weights (small positive)
    edge_widths = [max(0.2, G[u][v]['weight']*5) for u, v in G.edges()]
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes)
    nx.draw_networkx_edges(G, pos, width=edge_widths, arrowsize=12, arrowstyle='->')
    labels = {n: n.replace('https://', '').replace('http://', '') for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
    plt.axis('off')
    plt.title("Link network with edge weights = PageRank(source)")
    plt.tight_layout()
    plt.savefig(out_pdf)
    print(f"Saved visualization to {out_pdf}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Root URL to crawl (same-domain crawling)")
    parser.add_argument("--max-pages", type=int, default=100, help="Max pages to crawl (default 100)")
    parser.add_argument("--output", default="graph.pdf", help="Output PDF filename")
    args = parser.parse_args()
    G = crawl(args.root, args.max_pages)
    print(f"Crawled {len(G.nodes())} nodes and {len(G.edges())} edges")
    compute_and_visualize(G, args.output)

if __name__ == '__main__':
    main()

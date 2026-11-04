import collections
import datetime as dt
import html
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import urllib.parse

USER = 'Cmz9111'
ROOT = Path(__file__).resolve().parent

def api(path):
    token = os.environ.get('GH_TOKEN')
    if token:
        request = urllib.request.Request('https://api.github.com/' + path, headers={
            'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
            'User-Agent': 'Cmz9111-profile'})
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    return json.loads(subprocess.check_output(['gh', 'api', path], encoding='utf-8'))

def generate():
    query = urllib.parse.quote(f'is:pr is:merged author:{USER}')
    prs = []
    page = 1
    while True:
        result = api(f'search/issues?q={query}&per_page=100&page={page}')
        if result.get('incomplete_results') or result['total_count'] > 1000:
            raise RuntimeError('Search results incomplete; previous panel preserved')
        prs.extend(result['items'])
        if len(prs) >= result['total_count']:
            break
        page += 1
    merged = []
    for pr in prs:
        detail = api(pr['pull_request']['url'].split('api.github.com/')[1])
        if detail['merged_at']:
            merged.append((pr['repository_url'].split('/repos/')[1], dt.datetime.fromisoformat(detail['merged_at'].replace('Z', '+00:00'))))
    now = dt.datetime.now(dt.timezone.utc)
    recent = [(repo, date) for repo, date in merged if now - date < dt.timedelta(days=30)]
    external = sum(repo.split('/')[0].lower() != USER.lower() for repo, _ in merged)
    counts = collections.Counter(repo for repo, _ in merged)
    featured = [api(f'repos/{USER}/{name}') for name in ['pytorch-learning', 'FastAPI_first']]
    rows = counts.most_common(6)
    height = 1000 + max(len(rows), 1) * 64
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">陈民振 · GitHub 个人主页</title>',
             f'<desc id="desc">已合并 {len(merged)} 个 PR，近30天 {len(recent)} 个。PyTorch 与 FastAPI 学习项目。</desc>',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<style>text{font-family:Segoe UI,Arial,Microsoft YaHei,sans-serif;fill:#1f2328}.muted{fill:#697586}.label{fill:#8250df;font-family:monospace;letter-spacing:3px}.mono{font-family:monospace}</style>']
    def text(x, y, value, size=18, cls='', weight='400'):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" font-weight="{weight}">{html.escape(str(value))}</text>')
    def line(y):
        parts.append(f'<path d="M56 {y}H944" stroke="#e8ecf1"/>')
    text(56, 55, '▪ LEARNING IN PUBLIC · PYTHON', 13, 'label')
    text(56, 138, '陈民振', 48, weight='700')
    text(240, 138, '· Cmz9111', 40, 'muted')
    text(56, 195, '构建Coding Agent，也持续向一线AI开源仓库贡献代码', 21, 'muted')
    text(56, 230, '2028届研究生在读，专注Agent harness/MCP/多智能体系统', 16, 'muted')
    text(56, 330, '▪ MERGED PULL REQUESTS', 13, 'label')
    text(745, 330, 'github.com/Cmz9111', 13, 'muted')
    line(352)
    text(56, 440, len(merged), 72, weight='700')
    text(180, 440, '个 PR 已合并', 24, weight='600')
    text(56, 478, f'{external} 个提给他人仓库 · 近 30 天 +{len(recent)}', 16, 'muted')
    days = collections.Counter((date.date() - (now.date() - dt.timedelta(days=29))).days for _, date in recent)
    line(557)
    for day, count in days.items():
        if 0 <= day < 30:
            for index in range(min(count, 4)):
                parts.append(f'<circle cx="{62 + day * 30}" cy="{548 - index * 13}" r="4" fill="#8250df"/>')
            if count > 4:
                text(56 + day * 30, 490, count, 10, 'label')
    if not recent:
        text(56, 530, '近 30 天暂无已合并 PR', 15, 'muted')
    text(56, 585, (now.date() - dt.timedelta(days=29)).isoformat(), 12, 'muted')
    text(862, 585, now.date().isoformat(), 12, 'muted')
    y = 640
    if not rows:
        text(56, y, '开源贡献从下一次提交开始。', 18, 'muted')
        y += 64
    for repo, count in rows:
        stars = api('repos/' + repo)['stargazers_count']
        text(56, y, repo, 20, 'mono', '600')
        text(720, y, f'{count} 个 PR', 17)
        text(845, y, f'☆ {stars}', 15, 'muted')
        line(y + 24)
        y += 64
    text(56, y + 30, '▪ LEARNING PROJECTS', 13, 'label')
    for project in featured:
        y += 84
        text(56, y, project['name'], 23, 'mono', '600')
        text(56, y + 29, project['description'] or '', 16, 'muted')
        text(835, y, 'Python', 15, 'label')
    line(y + 58)
    text(56, y + 87, 'GitHub API · 每日自动更新', 12, 'muted')
    text(700, y + 87, now.strftime('%Y-%m-%d %H:%M UTC'), 12, 'muted')
    parts.append('</svg>')
    (ROOT / 'assets/profile.svg').write_text('\n'.join(parts), encoding='utf-8')
    print(f'Generated panel: {len(merged)} merged PRs, {len(recent)} recent')

if __name__ == '__main__':
    generate()

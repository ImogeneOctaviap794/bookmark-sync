from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import httpx
import asyncio
from bs4 import BeautifulSoup
import json

from models import User, get_db
from auth import get_current_user
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api", tags=["analyze"])

class ApiConfig(BaseModel):
    apiUrl: str
    apiKey: str
    apiModel: str = "gpt-4o-mini"

class AnalyzeRequest(BaseModel):
    urls: List[str]
    existingCategories: List[str] = []
    renameMode: str = "normal"  # normal, aggressive, conservative
    apiConfig: ApiConfig  # 从扩展传递的 API 配置

class AnalyzeResult(BaseModel):
    url: str
    success: bool
    title: Optional[str] = None
    suggestedName: Optional[str] = None
    suggestedCategory: Optional[str] = None
    isNewCategory: bool = False
    error: Optional[str] = None

class AnalyzeResponse(BaseModel):
    total: int
    success: int
    failed: int
    results: List[AnalyzeResult]

# 抓取单个网页
async def fetch_page(client: httpx.AsyncClient, url: str) -> dict:
    """抓取网页内容，返回提取的信息"""
    try:
        response = await client.get(
            url,
            follow_redirects=True,
            timeout=10.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        )
        
        if response.status_code != 200:
            return {'url': url, 'error': f'HTTP {response.status_code}'}
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取信息
        title = soup.title.string.strip() if soup.title and soup.title.string else ''
        
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = desc_tag.get('content', '').strip() if desc_tag else ''
        
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        keywords = keywords_tag.get('content', '').strip() if keywords_tag else ''
        
        h1_tag = soup.find('h1')
        h1 = h1_tag.get_text().strip() if h1_tag else ''
        
        # 提取正文
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            tag.decompose()
        
        text = ' '.join(soup.get_text().split())[:500]
        
        return {
            'url': url,
            'title': title,
            'description': description,
            'keywords': keywords,
            'h1': h1,
            'text': text,
            'success': True
        }
        
    except httpx.TimeoutException:
        return {'url': url, 'error': '请求超时'}
    except httpx.ConnectError:
        return {'url': url, 'error': '连接失败'}
    except Exception as e:
        return {'url': url, 'error': str(e)}

# 调用 AI 分析
async def analyze_with_ai(
    client: httpx.AsyncClient,
    page_content: dict,
    existing_categories: List[str],
    rename_mode: str,
    api_config: ApiConfig
) -> dict:
    """使用 AI 分析网页内容，生成建议"""
    
    folder_names = ', '.join(existing_categories) if existing_categories else '无'
    
    system_prompt = f"""你是书签整理专家。分析网页信息，生成有意义的书签名称和分类。

用户已有分类: {folder_names}

## 命名要求
1. 长度: 15-35字符，信息密度高
2. 必须体现页面的核心价值/用途
3. 示例:
   - ❌ "BettaFish - GitHub项目主页" (太空泛)
   - ✅ "微舆 - 多Agent舆情分析助手" (体现用途)

## 分类规则
优先匹配已有分类；无合适则建议新分类

## 输出
严格JSON: {{"name": "书签名称", "category": "分类名", "isNew": false}}"""

    user_content = f"""URL: {page_content.get('url', '')}
网页标题: {page_content.get('title', '')}
描述: {page_content.get('description', '')}
关键词: {page_content.get('keywords', '')}
H1: {page_content.get('h1', '')}
内容预览: {page_content.get('text', '')}"""

    try:
        response = await client.post(
            api_config.apiUrl,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_config.apiKey}'
            },
            json={
                'model': api_config.apiModel,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_content}
                ],
                'temperature': 0.3,
                'max_tokens': 150
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            return {'error': f'AI API 错误: {response.status_code}'}
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # 解析 JSON
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            result = json.loads(content[start:end])
            return {
                'suggestedName': result.get('name', ''),
                'suggestedCategory': result.get('category', ''),
                'isNewCategory': result.get('isNew', False)
            }
        
        return {'error': 'AI 返回格式错误'}
        
    except Exception as e:
        return {'error': f'AI 分析失败: {str(e)}'}

# 处理单个 URL
async def process_url(
    client: httpx.AsyncClient,
    url: str,
    existing_categories: List[str],
    rename_mode: str,
    api_config: ApiConfig,
    semaphore: asyncio.Semaphore
) -> AnalyzeResult:
    """处理单个 URL：抓取 + AI 分析"""
    async with semaphore:
        # 1. 抓取网页
        page_content = await fetch_page(client, url)
        
        if 'error' in page_content:
            return AnalyzeResult(
                url=url,
                success=False,
                error=page_content['error']
            )
        
        # 2. AI 分析
        ai_result = await analyze_with_ai(client, page_content, existing_categories, rename_mode, api_config)
        
        if 'error' in ai_result:
            return AnalyzeResult(
                url=url,
                success=False,
                title=page_content.get('title'),
                error=ai_result['error']
            )
        
        return AnalyzeResult(
            url=url,
            success=True,
            title=page_content.get('title'),
            suggestedName=ai_result.get('suggestedName'),
            suggestedCategory=ai_result.get('suggestedCategory'),
            isNewCategory=ai_result.get('isNewCategory', False)
        )

@router.post("/batch-analyze", response_model=AnalyzeResponse)
async def batch_analyze(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量分析书签 URL"""
    
    if len(req.urls) > 100:
        raise HTTPException(status_code=400, detail="最多支持 100 个 URL")
    
    # 并发限制
    semaphore = asyncio.Semaphore(10)
    
    async with httpx.AsyncClient() as client:
        tasks = [
            process_url(client, url, req.existingCategories, req.renameMode, req.apiConfig, semaphore)
            for url in req.urls
        ]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r.success)
    
    return AnalyzeResponse(
        total=len(results),
        success=success_count,
        failed=len(results) - success_count,
        results=results
    )

@router.post("/fetch-page")
async def fetch_single_page(
    url: str,
    current_user: User = Depends(get_current_user)
):
    """抓取单个网页内容（调试用）"""
    async with httpx.AsyncClient() as client:
        result = await fetch_page(client, url)
    return result

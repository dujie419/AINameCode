import asyncio
import json
import time
from urllib import request

import settings
from schemas.brand_visual import BrandVisualGenerateIn


class BailianService:
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.api_url = settings.DASHSCOPE_API_URL
        self.model = settings.DASHSCOPE_MODEL

    def build_brand_visual_prompt(self, data: BrandVisualGenerateIn):
        if data.mode == "card":
            return f"""
你是一位资深个人品牌顾问、名片视觉设计师和商务文案策划。
请根据用户提供的人名和诉求，生成一套个人名片方案，而不是品牌 Logo 方案。

姓名：{data.name}
身份/用途：{data.industry or "个人名片、个人品牌，请根据姓名和寓意合理推断"}
视觉风格：{data.style or "专业、清晰、有识别度"}
名字寓意：{data.meaning or "未填写，请根据姓名合理推断"}
目标受众：{data.target_users or "商务合作方、潜在客户、社交场合联系人"}
使用场景：{data.usage_scene or "线下递交、社交媒体头像、电子名片、个人主页"}

要求：
1. 输出必须是严格 JSON，不要使用 Markdown 代码块。
2. 这是个人名片方案，不要把结果写成 Logo 方案。
3. logo_concept 字段用于表达“名片视觉概念”，logo_prompt 字段用于表达“名片图片生成 Prompt”，不要生成单独 Logo。
4. business_card_layout 必须包含正面和背面排版建议。
5. card_image_prompt 要能直接给图片生成模型使用，描述横版名片、正反面、姓名层级、联系方式占位、颜色、字体、材质和构图。
6. contact_placeholders 输出 3 到 5 个占位项，例如手机号、邮箱、微信、职位、所在地。

JSON 字段如下：
{{
  "slogan": "",
  "logo_concept": "",
  "logo_prompt": "",
  "color_palette": [],
  "typography_style": "",
  "business_card_layout": "",
  "person_name": "",
  "title": "",
  "contact_placeholders": [],
  "front_layout": "",
  "back_layout": "",
  "card_image_prompt": "",
  "brand_story": "",
  "marketing_copy": "",
  "brand_visual_report": ""
}}
"""

        return f"""
你是一位资深品牌视觉策略顾问、Logo 创意总监和商业文案策划。
请根据用户提供的品牌信息，生成一套适合冷启动阶段使用的品牌视觉方案。

品牌名称：{data.name}
行业：{data.industry or "未填写，请根据品牌名合理推断"}
品牌调性：{data.style or "专业、清晰、有识别度"}
名字寓意：{data.meaning or "未填写，请根据品牌名合理推断"}
目标用户：{data.target_users or "未填写，请给出通用建议"}
使用场景：{data.usage_scene or "官网、App、名片、社交媒体、商业计划书"}

要求：
1. 输出必须是严格 JSON，不要使用 Markdown 代码块。
2. slogan 要短、有记忆点，适合中文品牌传播。
3. logo_prompt 要能直接给图片生成模型使用，描述构图、符号、颜色、材质、风格和禁忌。
4. color_palette 输出 4 到 6 个颜色，包含颜色名和 HEX。
5. marketing_copy 要像一键品牌冷启动方案，包含首发定位、传播话术和落地建议。

JSON 字段如下：
{{
  "slogan": "",
  "logo_concept": "",
  "logo_prompt": "",
  "color_palette": [],
  "typography_style": "",
  "business_card_layout": "",
  "brand_story": "",
  "marketing_copy": "",
  "brand_visual_report": ""
}}
"""

    async def generate_brand_visual(self, data: BrandVisualGenerateIn):
        prompt = self.build_brand_visual_prompt(data)
        if not self.api_key:
            return self._fallback_brand_visual(data)

        try:
            return await asyncio.to_thread(self._call_bailian_text, prompt)
        except Exception:
            return self._fallback_brand_visual(data)

    def _call_bailian_text(self, prompt: str):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你只输出严格 JSON。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }
        req = request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)

    def _fallback_brand_visual(self, data: BrandVisualGenerateIn):
        if data.mode == "card":
            style = data.style or "专业、现代、清晰"
            meaning = data.meaning or f"{data.name} 代表可靠的个人气质与持续成长。"
            title = data.industry or "个人品牌名片"
            colors = ["墨黑 #111827", "云白 #F8FAFC", "钴蓝 #2563EB", "银灰 #CBD5E1"]
            card_prompt = (
                f"为姓名“{data.name}”设计一张高级横版个人名片方案，身份为“{title}”，风格为{style}。"
                "画面包含正反面展示，正面突出姓名、身份/职位和一句短标语，背面包含手机号、邮箱、微信、个人主页等联系方式占位。"
                "使用清晰留白、现代中文字体、细腻纸张材质、克制配色，构图适合真实印刷名片预览。避免单独 Logo、复杂插画、低清晰度文字。"
            )
            return {
                "slogan": f"{data.name}，让专业被记住",
                "logo_concept": f"围绕“{meaning}”构建个人名片视觉，以姓名字形、留白层级和联系方式结构建立可信赖的第一印象。",
                "logo_prompt": card_prompt,
                "color_palette": colors,
                "typography_style": "中文建议使用现代黑体或宋黑结合，姓名使用较粗字重，联系方式使用中等字重并保持足够字距。",
                "business_card_layout": "正面左侧大字号展示姓名，右侧放身份/职位和短标语；背面使用品牌主色作为底色，分组展示电话、邮箱、微信和个人主页占位。",
                "person_name": data.name,
                "title": title,
                "contact_placeholders": ["手机号", "邮箱", "微信", "个人主页"],
                "front_layout": "正面：姓名为视觉中心，身份/职位置于姓名下方，右下角保留联系方式摘要。",
                "back_layout": "背面：使用主色块和细线分隔信息，纵向排列联系方式占位，保留二维码区域。",
                "card_image_prompt": card_prompt,
                "brand_story": f"{data.name} 的名片以“{meaning}”为核心，将个人气质转化为稳定、清晰、容易被记住的视觉触点。",
                "marketing_copy": "建议优先用于线下会面、电子名片和个人主页头像背景，保持姓名、身份、联系方式在不同场景中的一致表达。",
                "brand_visual_report": f"整体名片视觉应围绕{style}展开，突出姓名可读性、联系方式清晰度和正反面信息层级。",
            }

        industry = data.industry or "品牌服务"
        style = data.style or "专业、现代、清晰"
        meaning = data.meaning or f"{data.name} 代表可信赖的专业能力与持续成长。"
        slogan = f"{data.name}，让好想法被看见"
        colors = ["深海蓝 #123B63", "银灰 #C9D1D9", "晨雾白 #F7FAFC", "活力青 #18A0A6"]
        return {
            "slogan": slogan,
            "logo_concept": f"围绕“{data.name}”打造一个简洁、有识别度的品牌符号，突出{industry}的专业感，并呼应“{meaning}”。",
            "logo_prompt": (
                f"为中文品牌“{data.name}”设计一张高质量 Logo 概念图，行业为{industry}，品牌调性为{style}。"
                "使用简洁几何符号、清晰留白、现代商业品牌构图，主色为深海蓝与银灰，"
                "图形需适合 App 图标、官网页眉、名片和社交媒体头像。避免复杂插画、摄影质感、过多文字和低清晰度细节。"
            ),
            "color_palette": colors,
            "typography_style": "中文建议使用偏现代黑体或几何无衬线字体，字重中等偏粗；英文字体使用简洁 Sans Serif，保持科技与可信赖感。",
            "business_card_layout": "极简横版名片，左侧放品牌 Logo，右侧分层展示姓名、职位、电话、邮箱和官网；背面使用品牌主色和一句 Slogan。",
            "brand_story": f"{data.name} 以“{meaning}”为核心叙事，用更清晰的视觉语言帮助用户快速理解品牌价值。",
            "marketing_copy": f"冷启动阶段建议聚焦“{industry}中的专业新选择”，用 Logo、Slogan、官网首屏和社媒海报统一传达“{slogan}”。",
            "brand_visual_report": f"整体视觉应围绕{style}展开，优先建立统一色彩、稳定字体和可复用的 Logo 符号系统。",
        }

    async def generate_logo_image(self, logo_prompt: str):
        return await self.generate_image(logo_prompt=logo_prompt)

    async def generate_image(self, logo_prompt: str, size: str = "1024*1024", n: int = 1):
        if not self.api_key:
            return {
                "image_url": None,
                "task_id": None,
                "status": "NO_API_KEY",
                "message": "未配置 DASHSCOPE_API_KEY，无法调用图片生成接口。",
            }
        try:
            return await asyncio.to_thread(self._call_bailian_image, logo_prompt, size, n)
        except Exception as error:
            return {
                "image_url": None,
                "task_id": None,
                "status": "FAILED",
                "message": f"图片生成失败：{str(error)}",
            }

    def _call_bailian_image(self, logo_prompt: str, size: str, n: int):
        task_id = self._submit_image_task(logo_prompt=logo_prompt, size=size, n=n)
        task_result = self._wait_image_task(task_id=task_id)
        image_url = self._extract_image_url(task_result)
        status = self._extract_task_status(task_result)
        return {
            "image_url": image_url,
            "task_id": task_id,
            "status": status,
            "message": "图片生成成功" if image_url else "图片任务完成，但未解析到图片地址。",
        }

    def _submit_image_task(self, logo_prompt: str, size: str, n: int):
        payload = {
            "model": settings.DASHSCOPE_IMAGE_MODEL,
            "input": {
                "prompt": logo_prompt,
            },
            "parameters": {
                "size": size,
                "n": n,
            },
        }
        req = request.Request(
            settings.DASHSCOPE_IMAGE_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        task_id = result.get("output", {}).get("task_id") or result.get("task_id")
        if not task_id:
            raise ValueError(f"未获取到图片生成 task_id：{result}")
        return task_id

    def _wait_image_task(self, task_id: str, timeout_seconds: int = 180, interval_seconds: int = 3):
        deadline = time.time() + timeout_seconds
        last_result = None
        while time.time() < deadline:
            req = request.Request(
                f"{settings.DASHSCOPE_TASK_API_URL}/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                method="GET",
            )
            with request.urlopen(req, timeout=30) as response:
                last_result = json.loads(response.read().decode("utf-8"))
            status = self._extract_task_status(last_result)
            if status in {"SUCCEEDED", "FAILED", "CANCELED", "UNKNOWN"}:
                if status != "SUCCEEDED":
                    raise ValueError(f"图片生成任务未成功：{last_result}")
                return last_result
            time.sleep(interval_seconds)
        raise TimeoutError(f"图片生成任务超时：{last_result}")

    def _extract_task_status(self, task_result: dict):
        return (
            task_result.get("output", {}).get("task_status")
            or task_result.get("task_status")
            or task_result.get("status")
            or "UNKNOWN"
        )

    def _extract_image_url(self, task_result: dict):
        output = task_result.get("output", {})
        candidates = []
        for key in ("results", "task_results"):
            value = output.get(key) or task_result.get(key)
            if isinstance(value, list):
                candidates.extend(value)
        for item in candidates:
            if isinstance(item, dict):
                url = item.get("url") or item.get("image_url") or item.get("orig_url")
                if url:
                    return url
            elif isinstance(item, str):
                return item
        return output.get("url") or output.get("image_url") or task_result.get("image_url")

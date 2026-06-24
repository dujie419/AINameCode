import asyncio
from langchain_deepseek import ChatDeepSeek
from openai import timeout, max_retries
from pydantic import SecretStr
from langchain_core.prompts import ChatPromptTemplate
import settings

from schemas.name_schemas import NameSchema, NameResultSchema, NameIn

# 开发起名智能体
llm = ChatDeepSeek(
    model=settings.DEEPSEEK_MODEL,
    api_key=SecretStr(settings.DEEPSEEK_API_KEY),
    temperature=0.5,
    timeout=120
)

system_prompt ="""你是一位精通汉语言文学与传统文化的命名专家。请为用户创作富有文化底蕴的人名。
原则：平仄协调，寓意深远，优先从《诗经》《楚辞》或唐诗宋词中汲取灵感。
请给出 5 个候选方案。"""

prompt_template = ChatPromptTemplate([
    ("system", system_prompt),
    ("user", "【姓氏】:{surname} 【性别】:{gender} 【字数限制】:{length} 【其它要求】:{other} 【避讳字】:{exclude}")
])

structured_llm = llm.with_structured_output(NameResultSchema)

chain = prompt_template | structured_llm

# 生成名字：用户的要求
async def generate_names(name_info:NameIn):
    exclude_str = '、'.join(name_info.exclude) if name_info.exclude else '无'

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = chain.invoke(
                {
                    "surname":name_info.surname,
                    "gender":name_info.gender,
                    "length":name_info.length,
                    "other": name_info.other,
                    "exclude":exclude_str
                }
            )
            if result is not None:
                return result
            print(f'第{attempt+1}次模型未按规定输出，正在重试...')
        except Exception as e:
            print(e)
    raise ValueError("大模型服务器当前较拥挤")


# # 测试
# async def main():
#     name_info = NameIn(
#         surname="陈",
#         gender="女",
#         length="两字",
#         other="希望名字里带点水的意象",
#         exclude=["李", "王"]
#     )
#     names = await generate_names(name_info)
#     print("最终结果:", names)
#
#
# if __name__ == '__main__':
#     asyncio.run(main())

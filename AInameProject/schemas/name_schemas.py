from pydantic import BaseModel, Field, model_validator
from typing import Annotated,List,Literal

class NameSchema(BaseModel):
    name:Annotated[str,Field(...,description="姓名")]
    reference:Annotated[str,Field(...,description="出处")]
    moral:Annotated[str,Field(...,description="寓意")]
    domain:str = Field(...,description="为品牌设计纯小写.com域名，例如：astar.com")
    domain_status:str = Field(default="正在查询...",description="域名注册状态")

class NameResultSchema(BaseModel):
    names:List[NameSchema]
CategoryLiteral = Literal["人名","企业名","宠物名"]
class NameIn(BaseModel):
    category: Annotated[CategoryLiteral,Field(...,description="命名的分类")]
    surname:Annotated[str,Field("",description="The surname of the name")]
    gender:Annotated[Literal["不限","男","女"],Field("",description="The gender of the name")]
    length:Annotated[str,Field("",description="The length of the name")]
    other:Annotated[str|None,Field("",description="The other person")]
    exclude:Annotated[list[str]|None,Field([],description="The exclude person")]

    @model_validator(mode="after")
    def validate(self):
        if self.category == "人名" and not self.surname:
            raise ValueError("起名字必须有姓氏")
        # 用户调用NameIn，必定期望返回的是本对象
        return self


class NameOutSchema(BaseModel):
    names:List[NameSchema]


class NameOutSchemaWithThreadOut(BaseModel):
    thread_id: str
    name_record_id: int | None = None
    names:List[NameSchema]



# 为了调整需求，开发一个接收参数的类
class FeedbackSchema(BaseModel):
    thread_id:str = Field(...)
    category: Literal["人名", "企业名", "宠物名"] = Field(..., description="路由依据")
    feedback: str = Field(..., description="用户的修改意见，如：换成带水字旁的字")

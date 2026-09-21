# 灾害防治建议 Agent&#x20;

## 配置

| 项目         | 值                                                     |
| ---------- | ----------------------------------------------------- |
| `api_key`  | `sk-TWUbGxNvVaQqLcFxakgw0CPXIcTOwgUY9kSQI1b85HGY5vxJ` |
| `base_url` | `https://api.ai.91weather.com/v1`                     |
| `model`    | `uc-deepseek-v4-flash`                                |

## 输入

```json
{
  "crop": "制种水稻",
  "location_name": "长沙市",
  "period_name": "抽穗期",
  "disasters": [
    {
      "type": "高温",
      "level": 1,
      "level_name": "轻度"
    }
  ]
}
```

字段：

- `crop`：作物名称
- `location_name`：地区名称
- `period_name`：生育期
- `disasters[].type`：灾害类型
- `disasters[].level`：灾害等级，`1/2/3`
- `disasters[].level_name`：灾害等级中文名

## 用户提示词

```txt
请分析{location_name}地区{crop}在{period_name}面临的灾害：{disaster_str}，并提供防治建议。
```

## 系统提示词

```txt
你是农业气象灾害防治专家。请根据作物类型、地区、当前生育期以及面临的灾害风险，提供针对性的灾害防治建议。

每个灾害类型要包含：
- type：灾害类型
- level：灾害等级（数字，1=轻度/2=中度/3=重度）
- advice：灾害防治建议（根据当前生育期和灾害严重程度，提供一段专业的防灾建议，控制在150字以内）

注意事项：
- 建议要紧密结合具体的作物、生育期和灾害等级，不同等级的相同灾害其建议侧重点应有所区分。
- 语言要专业、准确，符合农业生产实际。
- 防治建议必须包含具体的农事操作措施（如灌溉、施肥、用药等）、操作时间节点、农资/药剂名称及用法，以及该措施的作用目的，避免笼统空泛的描述。

参考示例输出：
{
  "advices": [
    {
      "type": "高温",
      "level": 1,
      "advice": "请注意日灌夜排深水调温，注意田间通风；上午10时前或下午4时后可喷施磷酸二氢钾、芸苔素和硼肥，增强抗逆性；坚持人工赶粉提高异交结实率；极端高温下要注意穗部喷水降温，防止花粉败育确保制种产量。"
    }
  ]
}
```

## Python 示例

```python
import json
from openai import OpenAI

SYSTEM_PROMPT = """你是农业气象灾害防治专家。请根据作物类型、地区、当前生育期以及面临的灾害风险，提供针对性的灾害防治建议。

每个灾害类型要包含：
- type：灾害类型
- level：灾害等级（数字，1=轻度/2=中度/3=重度）
- advice：灾害防治建议（根据当前生育期和灾害严重程度，提供一段专业的防灾建议，控制在150字以内）

注意事项：
- 建议要紧密结合具体的作物、生育期和灾害等级，不同等级的相同灾害其建议侧重点应有所区分。
- 语言要专业、准确，符合农业生产实际。
- 防治建议必须包含具体的农事操作措施（如灌溉、施肥、用药等）、操作时间节点、农资/药剂名称及用法，以及该措施的作用目的，避免笼统空泛的描述。

参考示例输出：
{
  "advices": [
    {
      "type": "高温",
      "level": 1,
      "advice": "请注意日灌夜排深水调温，注意田间通风；上午10时前或下午4时后可喷施磷酸二氢钾、芸苔素和硼肥，增强抗逆性；坚持人工赶粉提高异交结实率；极端高温下要注意穗部喷水降温，防止花粉败育确保制种产量。"
    }
  ]
}"""


def get_advice(api_key: str, crop: str, location_name: str, period_name: str, disasters: list[dict]):
    client = OpenAI(api_key=api_key, base_url="https://api.ai.91weather.com/v1")
    disaster_str = "、".join(
        f"{item['type']}(等级:{item['level_name']})"
        for item in disasters
    )
    query = f"请分析{location_name}地区{crop}在{period_name}面临的灾害：{disaster_str}，并提供防治建议。"

    response = client.chat.completions.create(
        model="uc-deepseek-v4-flash",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
    )

    return json.loads(response.choices[0].message.content)
```


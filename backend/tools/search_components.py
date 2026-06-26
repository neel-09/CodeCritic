# import os, json, re
# from langchain_tavily import TavilySearch
# from backend.providers.router import fast_llm
# from backend.tools.circuit_validator import KNOWN_WOKWI_COMPONENTS
# from dotenv import load_dotenv
# load_dotenv()

# def get_content(result):
#         if isinstance(result, dict):
#             results_list = result.get("results", [])
#         elif isinstance(result, list):
#             results_list = result
#         else:
#             results_list = []
#         return "\n".join([r.get("content", "") for r in results_list[:2] if isinstance(r, dict)])

# def parse_llm_json(response):
#         try:
#             raw = response.content.strip()
#             raw = re.sub(r"```json\n|\n```|```", "", raw).strip()
#             return json.loads(raw)
#         except json.JSONDecodeError:    
#             return {}

# def search_component_specs(component_name: str) -> dict:

#     search = TavilySearch(max_results=2)
#     found_wokwi_id = None
#     datasheet_result = search.invoke(f"{component_name} site:alldatasheet.com pinout voltage protocol")
#     datasheet_content = get_content(datasheet_result)

#     if not datasheet_content:
#         return {
#             "wokwi_id": None,
#             "protocol": None, 
#             "voltage": None, 
#             "pinout": None, 
#             "datasheet_url": None, 
#             "i2c_address": None
#         }

#     datasheet_prompt = f"""Extract component specs for {component_name} from this text.
#     Return ONLY a JSON object with these fields: pinout, voltage, protocol, i2c_address.
#     If a field is unknown set it to null.
#     Do not include markdown, explanation, or any text outside the JSON object.
#     Text: {datasheet_content}"""

#     response2 = fast_llm.invoke(datasheet_prompt)
#     datasheet_data = parse_llm_json(response2)

#     datasheet_data["wokwi_id"] = found_wokwi_id
#     return datasheet_data

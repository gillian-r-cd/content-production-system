#!/bin/bash

PROJECT_ID="proj_20260202103009"
BASE_URL="http://localhost:8000/api/workflow"

echo "============================================"
echo "目录编辑功能完整测试"
echo "============================================"

echo ""
echo "=== 1. 获取当前目录结构 ==="
curl -s "$BASE_URL/$PROJECT_ID/outline" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'章节数: {len(d.get(\"sections\", []))}'); [print(f'  - {s[\"name\"]} ({len(s[\"fields\"])} fields)') for s in d.get('sections', [])]"

echo ""
echo "=== 2. 测试添加新章节 ==="
RESULT=$(curl -s -X POST "$BASE_URL/$PROJECT_ID/outline/add-section" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试章节：拖拽测试"}')
echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'添加结果: {\"success\" if \"sections\" in d else \"failed\"}')"

echo ""
echo "=== 3. 再次获取目录验证添加 ==="
curl -s "$BASE_URL/$PROJECT_ID/outline" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'章节数: {len(d.get(\"sections\", []))}'); [print(f'  - {s[\"name\"]} (order={s[\"order\"]}, {len(s[\"fields\"])} fields)') for s in d.get('sections', [])]"

echo ""
echo "=== 4. 测试向章节添加字段 ==="
# 首先获取第一个章节的ID
SECTION_ID=$(curl -s "$BASE_URL/$PROJECT_ID/outline" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['sections'][0]['id'] if d.get('sections') else '')")
echo "第一个章节ID: $SECTION_ID"

if [ -n "$SECTION_ID" ]; then
    RESULT=$(curl -s -X POST "$BASE_URL/$PROJECT_ID/outline/add-field" \
      -H "Content-Type: application/json" \
      -d "{\"section_id\": \"$SECTION_ID\", \"name\": \"test_field\", \"display_name\": \"测试字段\"}")
    echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); s=next((s for s in d.get('sections',[]) if s['id']=='$SECTION_ID'),None); print(f'字段数: {len(s[\"fields\"])}' if s else 'failed')"
fi

echo ""
echo "=== 5. 测试目录更新（模拟拖拽重排序） ==="
# 获取当前目录，交换前两个章节顺序
OUTLINE=$(curl -s "$BASE_URL/$PROJECT_ID/outline")
NEW_OUTLINE=$(echo "$OUTLINE" | python3 -c "
import json,sys
d=json.load(sys.stdin)
sections = d.get('sections', [])
if len(sections) >= 2:
    # 交换前两个章节的order
    sections[0]['order'], sections[1]['order'] = sections[1]['order'], sections[0]['order']
    # 重新排序
    sections.sort(key=lambda x: x['order'])
print(json.dumps({'sections': sections}))
")
echo "更新目录..."
RESULT=$(curl -s -X PATCH "$BASE_URL/$PROJECT_ID/outline" \
  -H "Content-Type: application/json" \
  -d "$NEW_OUTLINE")
echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'更新结果: {\"success\" if \"sections\" in d else d.get(\"detail\", \"failed\")}')"

echo ""
echo "=== 6. 验证更新后的顺序 ==="
curl -s "$BASE_URL/$PROJECT_ID/outline" | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'  {i}. {s[\"name\"]} (order={s[\"order\"]})') for i,s in enumerate(d.get('sections', []))]"

echo ""
echo "=== 7. 测试字段生成（无需确认目录） ==="
curl -s -X POST "$BASE_URL/$PROJECT_ID/generate-fields" \
  -H "Content-Type: application/json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'生成结果: {d.get(\"status\", d.get(\"detail\", \"unknown\"))}')"

echo ""
echo "=== 8. 测试标记过时API ==="
if [ -n "$SECTION_ID" ]; then
    FIELD_ID=$(curl -s "$BASE_URL/$PROJECT_ID/outline" | python3 -c "import json,sys; d=json.load(sys.stdin); s=next((s for s in d.get('sections',[]) if s['id']=='$SECTION_ID'),None); print(s['fields'][0]['id'] if s and s.get('fields') else '')")
    echo "字段ID: $FIELD_ID"
    if [ -n "$FIELD_ID" ]; then
        RESULT=$(curl -s -X POST "$BASE_URL/$PROJECT_ID/mark-stale" \
          -H "Content-Type: application/json" \
          -d "{\"modified_field_id\": \"$FIELD_ID\"}")
        echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'标记过时结果: {d}')"
    fi
fi

echo ""
echo "============================================"
echo "测试完成"
echo "============================================"

## DDD Guardrail

For any work touching `src/strategy/**`, use `.codex/skills/ddd-coding-guard` before implementation.
For hotspot cleanup or boundary repair in existing code, use `.codex/skills/ddd-refactor-coach`.

Redlines for `src/strategy/**` work:
- Domain code must not import infrastructure modules, framework types, or vendor payloads.
- Business rules must not be added to gateway, persistence, web, bootstrap, or runtime-entry layers.
- Cross-context handoffs must use explicit ports, DTOs, or value objects instead of mutable entities or raw vendor payloads.
- Do not add new facade or coordinator layers that flatten existing boundaries.

Read the full doctrine in:
- `docs/architecture/ddd-constitution.md`
- `docs/architecture/context-map.md`
- `docs/architecture/refactor-catalog.md`
# Agent 琛屼负瑙勮寖

## 鑷姩 Git 鎻愪氦瑙勫垯

褰撲綘瀹屾垚浠ヤ笅浠讳綍涓€绫绘搷浣滃悗锛屽繀椤昏嚜鍔ㄦ墽琛?`git add {淇敼鐨勬枃浠秨`銆乣git commit -m "<message>"`銆乣git push`锛?

1. 淇 bug 鎴栭敊璇紙濡傚鍏ヨ矾寰勪慨澶嶃€佽繍琛屾椂鎶ラ敊淇锛?
2. 鏂板鍔熻兘鎴栨枃浠?
3. 閲嶆瀯浠ｇ爜锛堝閲嶅懡鍚嶃€佺Щ鍔ㄦ枃浠躲€佽皟鏁寸粨鏋勶級
4. 淇敼閰嶇疆鏂囦欢锛堝 Dockerfile銆乸ytest.ini銆乺equirements.txt 绛夛級
5. 鏇存柊鎴栨柊澧炴祴璇?
6. 鏇存柊鏂囨。锛堝 README銆侀渶姹傛枃妗ｃ€丄GENTS.md 绛夛級

## Commit 娑堟伅鏍煎紡

浣跨敤涓枃锛岄伒寰?Conventional Commits 椋庢牸锛?

```
<type>: <绠€瑕佹弿杩?

<鍙€夌殑璇︾粏璇存槑>
```

type 鍙栧€硷細
- `fix`: 淇 bug
- `feat`: 鏂板姛鑳?
- `refactor`: 閲嶆瀯
- `docs`: 鏂囨。鍙樻洿
- `chore`: 鏋勫缓/閰嶇疆/宸ュ叿鍙樻洿
- `test`: 娴嬭瘯鐩稿叧
- `style`: 鏍煎紡璋冩暣锛堜笉褰卞搷閫昏緫锛?

## 娉ㄦ剰浜嬮」

- 姣忔鎿嶄綔瀹屾垚鍚庣珛鍗虫彁浜わ紝涓嶈绉敀澶氫釜涓嶇浉鍏崇殑鍙樻洿鍒颁竴涓?commit
- commit 娑堟伅瑕佸噯纭弿杩版湰娆″彉鏇村唴瀹?
- 濡傛灉涓€娆＄敤鎴疯姹傛秹鍙婂涓笉鐩稿叧鐨勬敼鍔紝鎷嗗垎涓哄涓?commit
- 如果检测到 .codex 的 skill 有增加，也请顺手进行 commit 并推送，commit消息类似 “chore: 增加{skill名} skill”


姝ら」鐩湭閮ㄧ讲锛岃涓嶈鑰冭檻浠讳綍鍚戝悗鍏煎鎬э紝鐩存帴澶ц儐鏀惧績鏀规帴鍙ｃ€佹敼schema绛?


閽堝棰嗗煙鏈嶅姟鎴栬€呭熀纭€璁炬柦锛屼笉瑕佸啓 facade, coordinator 涓€绫荤殑浠ｇ爜锛岀洿鎺ヨ涓婂眰璋冪敤鍏蜂綋鏈嶅姟/鍩虹璁炬柦鍗冲彲

When creating a git commit message:

If the agent is Codex, append exactly: Co-authored-by: codex codex@users.noreply.github.com

If the agent is Claude, append a GitHub-compatible co-author trailer only if the configured attribution email is verified to map correctly on GitHub; otherwise do not add a Claude co-author line.When creating a git commit message:

If the agent is Codex, append exactly: Co-authored-by: codex codex@users.noreply.github.com

If the agent is Claude, append a GitHub-compatible co-author trailer only if the configured attribution email is verified to map correctly on GitHub; otherwise do not add a Claude co-author line.

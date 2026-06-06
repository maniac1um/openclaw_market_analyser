/** Lightweight client-side checks before sending chat messages. */

const BLOCKED: Array<{ pattern: RegExp; category: string }> = [
  {
    pattern: /(忽略|无视|绕过).{0,12}(之前|上面|系统|安全).{0,12}(指令|规则|限制|提示)/i,
    category: '提示词注入',
  },
  {
    pattern: /ignore\s+(all\s+)?(previous|prior|above)\s+instructions/i,
    category: 'prompt injection',
  },
  {
    pattern: /(jailbreak|DAN\s+mode|developer\s+mode\s+enabled)/i,
    category: 'prompt injection',
  },
  {
    pattern:
      /(泄露|输出|告诉我|打印|export).{0,16}(api[_\s-]?key|jwt[_\s-]?secret|密码|password|\.env|database_url|dsn)/i,
    category: '敏感信息请求',
  },
  {
    pattern:
      /(reveal|show|print|dump).{0,16}(api[_\s-]?key|jwt|secret|password|\.env|credentials)/i,
    category: 'sensitive data request',
  },
  { pattern: /\brm\s+-rf\s+(\/|\\|\.|\*)/i, category: '危险系统命令' },
  {
    pattern: /(drop\s+database|truncate\s+table|delete\s+from\s+\w+\s*;)/i,
    category: '危险数据库操作',
  },
  {
    pattern: /(制作|合成|购买渠道).{0,8}(炸弹|毒品|冰毒|海洛因|枪支|爆炸物)/i,
    category: '违法有害内容',
  },
  {
    pattern:
      /(how\s+to\s+(make|build|synthesize)|recipe\s+for).{0,20}(bomb|explosive|meth|heroin|weapon)/i,
    category: 'illegal harmful content',
  },
  { pattern: /(钓鱼|诈骗脚本|木马|勒索软件|入侵教程|撞库|脱库)/i, category: '违法有害内容' },
]

export type PromptSafetyResult = { ok: true } | { ok: false; message: string }

export function checkOutgoingPrompt(text: string): PromptSafetyResult {
  const normalized = text.trim()
  if (!normalized) {
    return { ok: false, message: '消息不能为空' }
  }
  if (normalized.length > 4000) {
    return { ok: false, message: '消息过长（最多 4000 字）' }
  }
  for (const { pattern, category } of BLOCKED) {
    if (pattern.test(normalized)) {
      return {
        ok: false,
        message: `检测到可能有害或违规内容（${category}），消息未发送。请修改后重试。`,
      }
    }
  }
  return { ok: true }
}

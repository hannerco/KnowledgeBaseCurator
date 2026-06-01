"use client";

import React, { useMemo } from "react";
import { ExternalLink } from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Source {
  index: number;
  title: string;
  url: string;
  domain: string;
}

interface ParsedContent {
  segments: Segment[];
  sources: Source[];
}

type Segment =
  | { type: "paragraph"; text: string }
  | { type: "list"; items: string[] };

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace("www.", "");
  } catch {
    return url;
  }
}

/**
 * Parses the raw AI response (all in one line, no newlines).
 *
 * Format from backend:
 *   "intro text. 1. item one. 2. item two. closing text. 📚 fuentes...: 1. Title URL 2. Title URL"
 */
function parseContent(raw: string): ParsedContent {
  // 1. Split off sources section
  const sourceSplitIdx = raw.search(/📚|fuentes?\s+consultadas?/i);
  const body =
    sourceSplitIdx !== -1 ? raw.slice(0, sourceSplitIdx).trim() : raw.trim();
  const sourcesRaw = sourceSplitIdx !== -1 ? raw.slice(sourceSplitIdx) : "";

  // 2. Parse sources — each source: number. title url
  const sources: Source[] = [];
  if (sourcesRaw) {
    // Strip the "📚 fuentes consultadas en internet:" header
    const cleaned = sourcesRaw.replace(
      /📚\s*fuentes?\s+consultadas?[^:]*:?\s*/i,
      "",
    );
    // Match: "1. Some title https://..." up to the next "2." or end
    const sourceRegex = /(\d+)\.\s+([\s\S]*?)(?=\s+\d+\.\s+|$)/g;
    let m: RegExpExecArray | null;
    while ((m = sourceRegex.exec(cleaned)) !== null) {
      const idx = parseInt(m[1]);
      const block = m[2].trim();
      const urlMatch = block.match(/https?:\/\/\S+/);
      if (!urlMatch) continue;
      const url = urlMatch[0];
      const title =
        block
          .replace(url, "")
          .replace(/\|\s*$/, "")
          .trim() || url;
      sources.push({ index: idx, title, url, domain: extractDomain(url) });
    }
  }

  // 3. Parse body into segments
  // Strategy: split on numbered list patterns "1. " "2. " etc. that appear mid-sentence
  // We'll tokenize the body into runs of: plain text | numbered list groups
  const segments: Segment[] = [];

  // Split body on transitions: text before "1.", then list items, then closing text
  // Pattern: detect "N. text" sequences
  const listPattern = /(?<!\d)(\d+)\.\s+/g;

  // Find all positions of "N. " in the body
  const matches: { index: number; num: number; textStart: number }[] = [];
  let lm: RegExpExecArray | null;
  while ((lm = listPattern.exec(body)) !== null) {
    matches.push({
      index: lm.index,
      num: parseInt(lm[1]),
      textStart: lm.index + lm[0].length,
    });
  }

  if (matches.length === 0) {
    // No lists at all, just paragraphs
    splitIntoParagraphs(body).forEach((t) =>
      segments.push({ type: "paragraph", text: t }),
    );
    return { segments, sources };
  }

  // Group consecutive numbered items (1,2,3...) as a list
  // Non-consecutive numbers restart a new paragraph
  let cursor = 0;
  let i = 0;

  while (i < matches.length) {
    const cur = matches[i];

    // Text before this numbered item
    if (cur.index > cursor) {
      const pre = body.slice(cursor, cur.index).trim();
      if (pre) {
        splitIntoParagraphs(pre).forEach((t) =>
          segments.push({ type: "paragraph", text: t }),
        );
      }
    }

    // Collect consecutive list items starting at cur.num
    const listItems: string[] = [];
    let expected = cur.num;
    let j = i;

    while (j < matches.length && matches[j].num === expected) {
      const end = j + 1 < matches.length ? matches[j + 1].index : body.length;
      const itemText = body
        .slice(matches[j].textStart, end)
        .trim()
        .replace(/\.\s*$/, "");
      listItems.push(itemText);
      expected++;
      j++;
    }

    segments.push({ type: "list", items: listItems });
    cursor = j < matches.length ? matches[j].index : body.length;

    // Check for closing text between end of list and next list (or end)
    i = j;
  }

  // Remaining text after last list
  if (cursor < body.length) {
    const tail = body.slice(cursor).trim();
    if (tail) {
      splitIntoParagraphs(tail).forEach((t) =>
        segments.push({ type: "paragraph", text: t }),
      );
    }
  }

  return { segments, sources };
}

/** Capitalize first letter of a string */
function capitalize(text: string): string {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Pick a leading emoji based on paragraph content */
function getEmoji(text: string): string {
  const t = text.toLowerCase();
  if (/en resumen|resumiendo|conclu|en definitiva/.test(t)) return "💡";
  if (/ejemplo|por ejemplo|instancia/.test(t)) return "📌";
  if (/importante|destacar|notar|tener en cuenta/.test(t)) return "⚠️";
  if (/historia|origen|antigü|época|siglo/.test(t)) return "📜";
  if (/ciencia|física|química|biolog|electr|corriente|voltaje|circuito/.test(t))
    return "🔬";
  if (/aplicacion|utiliza|uso |usos|funciona/.test(t)) return "⚙️";
  if (/cultura|social|arte|música|teatro/.test(t)) return "🎭";
  if (/salud|médic|enfermed|protecci/.test(t)) return "🏥";
  if (/tipos?|categoría|clase|variedad/.test(t)) return "📋";
  return "📝";
}

/** Split a chunk of text into sentence-level paragraphs on ". " boundaries for readability */
function splitIntoParagraphs(text: string): string[] {
  return [text.trim()].filter(Boolean);
}

/** Render inline **bold** */
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i} className="font-semibold text-gray-900">
        {part.slice(2, -2)}
      </strong>
    ) : (
      part
    ),
  );
}

// ─── Component ────────────────────────────────────────────────────────────────

export function MessageContent({ content }: { content: string }) {
  const { segments, sources } = useMemo(() => parseContent(content), [content]);

  return (
    <div className="text-sm leading-relaxed text-gray-800 space-y-2">
      {segments.map((seg, i) =>
        seg.type === "paragraph" ? (
          <p key={i}>
            <span className="mr-1.5">{getEmoji(seg.text)}</span>
            {renderInline(capitalize(seg.text))}
          </p>
        ) : (
          <ol key={i} className="list-decimal list-outside pl-5 space-y-1">
            {seg.items.map((item, ii) => (
              <li key={ii}>{renderInline(capitalize(item))}</li>
            ))}
          </ol>
        ),
      )}

      {sources.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
            📚 Fuentes consultadas
          </p>
          <div className="space-y-1.5">
            {sources.map((src) => (
              <a
                key={src.index}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-2 px-2.5 py-2 rounded-lg bg-blue-50 border border-blue-100
                           hover:bg-blue-100 hover:border-blue-300 transition-colors group"
              >
                <span
                  className="text-[10px] font-bold text-blue-600 bg-blue-100 border border-blue-200
                                 rounded px-1.5 py-0.5 shrink-0 mt-0.5"
                >
                  {src.index}
                </span>
                <span className="flex-1 min-w-0">
                  <span className="block text-xs font-medium text-blue-700 group-hover:text-blue-900 leading-snug">
                    {src.title}
                  </span>
                  <span className="block text-[10px] text-gray-400 mt-0.5">
                    {src.domain}
                  </span>
                </span>
                <ExternalLink className="h-3 w-3 text-blue-400 shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

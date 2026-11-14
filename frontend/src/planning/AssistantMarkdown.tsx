import Markdown from 'react-markdown'

const formatting = [
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ol', 'ul', 'li',
  'strong', 'em', 'code', 'pre', 'blockquote', 'br', 'hr',
]

export function AssistantMarkdown({ text }: { text: string }) {
  return (
    <div className="assistant-markdown">
      <Markdown skipHtml allowedElements={formatting} unwrapDisallowed>{text}</Markdown>
    </div>
  )
}

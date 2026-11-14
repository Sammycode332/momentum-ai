import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import { AssistantMarkdown } from './AssistantMarkdown'

it('renders headings, paragraphs, lists, emphasis, and code', () => {
  const { container } = render(<AssistantMarkdown text={[
    '## Next steps', '', 'Use **bold**, *italic*, and `print()`.', '',
    '1. Draft', '2. Review', '', '- Check the result', '',
    '```python', 'print("ready")', '```',
  ].join('\n')} />)
  expect(screen.getByRole('heading', { name: 'Next steps' })).toBeInTheDocument()
  expect(container.querySelector('strong')).toHaveTextContent('bold')
  expect(container.querySelector('em')).toHaveTextContent('italic')
  expect(container.querySelector('p code')).toHaveTextContent('print()')
  expect(container.querySelectorAll('ol li')).toHaveLength(2)
  expect(container.querySelector('ul li')).toHaveTextContent('Check the result')
  expect(container.querySelector('pre code')).toHaveTextContent('print("ready")')
})

it('discards raw HTML and prevents executable links or external image loads', () => {
  const { container } = render(<AssistantMarkdown text={[
    '<script>alert(1)</script>', '', '<img src=x onerror=alert(1)>', '',
    '[click](javascript:alert%281%29) ![tracker](https://example.test/pixel)',
  ].join('\n')} />)
  expect(container.querySelector('script,img,a,[onerror]')).toBeNull()
  expect(screen.getByText('click')).toBeInTheDocument()
})

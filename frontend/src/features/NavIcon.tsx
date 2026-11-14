const paths: Record<string, string> = {
  home: 'm3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z',
  assistant: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z',
  projects: 'M3 7V5a1 1 0 0 1 1-1h5l2 3h9a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7z',
  tasks: 'm3 6 2 2 4-4M12 6h9M3 13l2 2 4-4m3 2h9M3 20l2 2 4-4m3 2h9',
  goals: 'M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9zm-4 0a5 5 0 1 1-5-5 5 5 0 0 1 5 5zm-4 0h-2',
  learning: 'M12 5C8 2 4 3 2 4v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-2-1-6-2-10 1zm0 0v15',
  academics: 'm2 8 10-5 10 5-10 5zM6 10v7c4 3 8 3 12 0v-7m4-2v9',
  opportunities: 'M9 5V3h6v2M3 7h18v14H3zm0 6c6 3 12 3 18 0m-9 1v3',
  notifications: 'M6 8a6 6 0 0 1 12 0v6l3 4H3l3-4zm4 13h4',
  settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm0-6v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2',
}
export function NavIcon({ name }: { name: string }) { return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] || paths.home} /></svg> }

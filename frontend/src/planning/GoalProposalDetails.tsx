import type { GoalDetails, Roadmap } from './conversation-api'

export function GoalProposalDetails({ goal, roadmap, selected, toggle, disabled }: {
  goal: GoalDetails
  roadmap?: Roadmap | null
  selected: number[]
  toggle?: (index: number) => void
  disabled: boolean
}) {
  return <>
    {goal.description && <p>{goal.description}</p>}
    {goal.target_date && <p>Target date {goal.target_date}</p>}
    {(goal.description || goal.target_date) && <p className="state-copy">Goals saves the title. The description and target date are kept in this proposal.</p>}
    {roadmap && <>
      <p>Estimated budget: {roadmap.weekly_hours} hours per week.</p>
      <p>{toggle ? 'Choose the phases to save with the goal. Clear all phases to save only the goal. Review earlier phases for prerequisites before skipping them.' : 'Roadmap phases'}</p>
      <ol>
        {roadmap.stages.map((stage, index) => <li key={index}>
          {toggle && <label><input type="checkbox" checked={selected.includes(index)} disabled={disabled}
            onChange={() => toggle(index)} /> Save phase {index + 1}</label>}
          <h5>{stage.milestone} · {stage.deadline}</h5>
          <p>{stage.project} · {stage.deliverable}</p>
          {stage.prerequisite && <p>Prerequisite: {stage.prerequisite}</p>}
          <ul>{stage.tasks.map((task, taskIndex) => <li key={taskIndex}>
            {task.title} · {task.due_date} · {task.hours}h estimated
          </li>)}</ul>
        </li>)}
      </ol>
    </>}
  </>
}

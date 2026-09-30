import { useQueryClient } from '@tanstack/react-query'

/**
 * Obnoví všetko, čo sa odvíja od harmonogramu projektu.
 *
 * Zmena trvania jednej úlohy prepíše kritickú cestu celého projektu, takže
 * nestačí obnoviť zoznam úloh — inak zostane napríklad záložka PERT alebo
 * rizikové skóre na starých číslach, kým používateľ stránku neobnoví ručne.
 *
 * Kľúče sa porovnávajú podľa predpony, takže `['pert', projectId]` zhodí aj
 * `['pert', projectId, deadline]` pre ľubovoľný termín.
 */
export function useScheduleRefresh(projectId: number) {
  const qc = useQueryClient()

  return (taskId?: number) => {
    // Zoznam úloh drží ES/EF/LS/LF a kritickosť — z neho čerpá tabuľka,
    // Ganttov diagram, sieťový diagram aj burndown.
    qc.invalidateQueries({ queryKey: ['tasks', projectId] })
    qc.invalidateQueries({ queryKey: ['project', projectId] })
    qc.invalidateQueries({ queryKey: ['pert', projectId] })
    qc.invalidateQueries({ queryKey: ['risk-score', projectId] })
    qc.invalidateQueries({ queryKey: ['resources', projectId] })

    // Trvanie projektu vstupuje aj do prehľadu naprieč projektmi a do kalendára.
    qc.invalidateQueries({ queryKey: ['portfolio'] })
    qc.invalidateQueries({ queryKey: ['calendar-tasks'] })

    if (taskId !== undefined) {
      qc.invalidateQueries({ queryKey: ['task-detail', taskId] })
    }
  }
}

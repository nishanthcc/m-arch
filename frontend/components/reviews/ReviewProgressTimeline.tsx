import React from 'react';
import { AgentTask } from '@/lib/types';
import { Badge } from '../ui/Badge';

interface ReviewProgressTimelineProps {
  tasks: AgentTask[];
  overallStatus: string;
}

export const ReviewProgressTimeline: React.FC<ReviewProgressTimelineProps> = ({
  tasks,
  overallStatus,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '20px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ fontSize: '14px', fontWeight: 600, letterSpacing: '0.02em' }}>
          A2A Multi-Agent Execution Progress
        </h4>
        <Badge variant="status" value={overallStatus}>
          {overallStatus}
        </Badge>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
        {tasks.map((task) => (
          <div
            key={task.id || task.agent_id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 14px',
              backgroundColor: 'var(--bg-elevated)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Badge variant="status" value={task.status}>
                {task.status}
              </Badge>
              <div>
                <span style={{ fontSize: '13px', fontWeight: 600 }}>{task.task_name}</span>
                <span
                  className="mono"
                  style={{ fontSize: '11px', color: 'var(--text-secondary)', marginLeft: '8px' }}
                >
                  ({task.agent_id})
                </span>
              </div>
            </div>

            <div
              className="mono"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                fontSize: '11px',
                color: 'var(--text-secondary)',
              }}
            >
              {task.provider_used && (
                <span>
                  Provider: <strong style={{ color: 'var(--text-primary)' }}>{task.provider_used}</strong> ({task.model_used})
                </span>
              )}
              {task.execution_time_seconds > 0 && (
                <span>{task.execution_time_seconds.toFixed(2)}s</span>
              )}
              {task.error_message && (
                <span style={{ color: 'var(--severity-critical)' }}>{task.error_message}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

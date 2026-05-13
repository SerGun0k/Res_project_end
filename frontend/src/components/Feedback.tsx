import { useState } from 'react';
import api from '../api/client';

interface FeedbackProps {
  productId: number;
  alternativeId?: number;
}

export default function Feedback({ productId, alternativeId }: FeedbackProps) {
  const [feedback, setFeedback] = useState<'useful' | 'not_useful' | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const submitFeedback = async (type: 'useful' | 'not_useful') => {
    try {
      await api.post('/feedback', {
        product_id: productId,
        feedback_type: type,
        alternative_id: alternativeId || null,
      });
      setFeedback(type);
      setSubmitted(true);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  if (submitted) {
    return (
      <div className="text-center text-sm text-slate-500 dark:text-slate-400 py-2">
        {feedback === 'useful'
          ? '✅ Спасибо за ваш отзыв!'
          : '📝 Мы учтём ваше мнение'}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 py-2">
      <span className="text-sm text-slate-600 dark:text-slate-400">Полезно?</span>
      <button
        onClick={() => submitFeedback('useful')}
        className="px-3 py-1 text-xs rounded-full border border-green-300 dark:border-green-700 text-green-700 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-900/40 transition"
      >
        👍 Да
      </button>
      <button
        onClick={() => submitFeedback('not_useful')}
        className="px-3 py-1 text-xs rounded-full border border-red-300 dark:border-red-700 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40 transition"
      >
        👎 Нет
      </button>
    </div>
  );
}

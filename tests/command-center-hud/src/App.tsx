import React from 'react';
import { WelcomeScreen } from './components/WelcomeScreen';

const App: React.FC = () => {
  const handleStartSession = (message: string, selectedIds: string[]) => {
    console.log('Session Initiated:', { message, selectedIds });
    alert(`COMMAND RECEIVED:\n"${message}"\n\nUNITS DEPLOYED: ${selectedIds.join(', ')}`);
    // In a real app, this would route to the Stage/Chat view
  };

  return (
    <div className="w-full h-screen bg-hud-bg">
      <WelcomeScreen onStartSession={handleStartSession} />
    </div>
  );
};

export default App;
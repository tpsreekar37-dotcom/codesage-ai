import React, { useState, useEffect } from 'react';

export const UserDashboard: React.FC = () => {
    const [data, setData] = useState<any>(null);
    const [counter, setCounter] = useState(0);

    // Infinite loop smell: missing dependency array
    useEffect(() => {
        fetch('/api/user')
            .then(res => res.json())
            .then(resData => {
                setData(resData);
                setCounter(c => c + 1);
            });
    });

    return (
        <div>
            <h1>Dashboard (Counter: {counter})</h1>
            <button onClick={() => console.log('clicked')}>Click</button>
        </div>
    );
};

import { useEffect, useState } from 'react';
import { Item, fetchItems } from '~/api';

const PLACEHOLDER_IMAGE = import.meta.env.VITE_FRONTEND_URL + '/logo192.png';

interface Prop {
  reload: boolean;
  onLoadCompleted: () => void;
}

export const ItemList = ({ reload, onLoadCompleted }: Prop) => {
  const [items, setItems] = useState<Item[]>([]);
  useEffect(() => {
    const fetchData = () => {
      fetchItems()
        .then((data) => {
          console.debug('GET success:', data);
          setItems(data.items);
          onLoadCompleted();
        })
        .catch((error) => {
          console.error('GET error:', error);
        });
    };

    if (reload) {
      fetchData();
    }
  }, [reload, onLoadCompleted]);

  return (

    <div className="ItemList">
      {items.map((item) => (
        <div key={item.id} className="itemCard">
          <img
            src={item.image_name ? `${import.meta.env. VITE_BACKEND_URL}/images/${item.image_name}` : PLACEHOLDER_IMAGE}
          />
          <div className="item-info">
            <h3>{item.name}</h3>
            <p>{item.category}</p>

          </div>
        </div>
      ))}
    </div>
  );
};

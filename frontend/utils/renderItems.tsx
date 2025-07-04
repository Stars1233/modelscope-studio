import { ContextPropsProvider } from '@svelte-preprocess-react/context';
import { ReactSlot } from '@svelte-preprocess-react/react-slot';
import React from 'react';

import { type Item } from './createItemsContext';
import { patchSlotProps } from './patchProps';

export function renderItems<R>(
  items: Item[],
  options?: {
    children?: string;
    fallback?: (item: any) => R;
    clone?: boolean;
    forceClone?: boolean;
    itemPropsTransformer?: (props: Record<string, any>) => Record<string, any>;
  },
  key?: React.Key
): undefined | R[] {
  const filterItems = items.filter(Boolean);
  if (filterItems.length === 0) {
    return undefined;
  }
  return filterItems.map((item, i) => {
    if (typeof item !== 'object') {
      if (options?.fallback) {
        return options.fallback(item);
      }
      return item;
    }
    const result = options?.itemPropsTransformer
      ? options?.itemPropsTransformer({
          ...item.props,
          key: item.props?.key ?? (key ? `${key}-${i}` : `${i}`),
        })
      : {
          ...item.props,
          key: item.props?.key ?? (key ? `${key}-${i}` : `${i}`),
        };

    let current = result;
    Object.keys(item.slots).forEach((slotKey) => {
      if (
        !item.slots[slotKey] ||
        (!(item.slots[slotKey] instanceof Element) && !item.slots[slotKey].el)
      ) {
        return;
      }

      const splits = slotKey.split('.');
      splits.forEach((split, index) => {
        if (!current[split]) {
          current[split] = {};
        }
        if (index !== splits.length - 1) {
          current = result[split];
        }
      });
      const elOrObject = item.slots[slotKey];

      let el: HTMLElement | undefined;
      let callback: ((key: string, params: any[]) => void) | undefined;
      let clone = options?.clone ?? false;
      let forceClone = options?.forceClone;
      if (elOrObject instanceof Element) {
        el = elOrObject;
      } else {
        el = elOrObject.el;
        callback = elOrObject.callback;
        clone = elOrObject.clone ?? clone;
        forceClone = elOrObject.forceClone ?? forceClone;
      }

      forceClone = forceClone ?? (callback ? true : false);
      current[splits[splits.length - 1]] = el
        ? callback
          ? (...args: any[]) => {
              callback(splits[splits.length - 1], args);

              return (
                <ContextPropsProvider
                  {...item.ctx}
                  params={args}
                  forceClone={forceClone}
                >
                  <ReactSlot slot={el} clone={clone} />
                </ContextPropsProvider>
              );
            }
          : patchSlotProps((props) => {
              return (
                <ContextPropsProvider {...item.ctx} forceClone={forceClone}>
                  <ReactSlot {...props} slot={el} clone={clone} />
                </ContextPropsProvider>
              );
            })
        : current[splits[splits.length - 1]];

      current = result;
    });
    const childrenKey = options?.children || 'children';
    if (item[childrenKey as keyof typeof item]) {
      result[childrenKey] = renderItems(
        item[childrenKey as keyof typeof item] as Item[],
        options,
        `${i}`
      );
    } else {
      if (options?.children) {
        result[childrenKey] = undefined;
        Reflect.deleteProperty(result, childrenKey);
      }
    }
    return result as R;
  }) as R[];
}

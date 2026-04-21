import { sveltify } from '@svelte-preprocess-react';
import { useEffect } from 'react';
import { useFunction } from '@utils/hooks/useFunction';
import { useMemoizedEqualValue } from '@utils/hooks/useMemoizedEqualValue';
import { useMemoizedFn } from '@utils/hooks/useMemoizedFn';
import { renderParamsSlot } from '@utils/renderParamsSlot';
import { Form as AForm, type GetProps } from 'antd';

export interface FormProps extends GetProps<typeof AForm> {
  value?: Record<string, any>;
  onValueChange: (value: Record<string, any>) => void;
  formAction?: 'reset' | 'submit' | 'validate' | null;
  onResetFormAction: () => void;
}

export const Form = sveltify<FormProps, ['requiredMark']>(
  ({
    value,
    formAction,
    onValueChange,
    requiredMark,
    onValuesChange,
    feedbackIcons,
    slots,
    onResetFormAction,
    children,
    ...props
  }) => {
    const [form] = AForm.useForm();
    const feedbackIconsFunction = useFunction(feedbackIcons);
    const requiredMarkFunction = useFunction(requiredMark);
    const onResetFormActionMemoized = useMemoizedFn(onResetFormAction);
    const valueMemoized = useMemoizedEqualValue(value);
    useEffect(() => {
      switch (formAction) {
        case 'reset':
          form.resetFields();
          break;
        case 'submit':
          form.submit();
          break;
        case 'validate':
          form.validateFields();
          break;
      }
      onResetFormActionMemoized();
    }, [form, formAction, onResetFormActionMemoized]);

    useEffect(() => {
      if (valueMemoized) {
        form.setFieldsValue(valueMemoized);
      } else {
        form.resetFields();
      }
    }, [form, valueMemoized]);

    return (
      <AForm
        {...props}
        form={form}
        requiredMark={
          slots.requiredMark
            ? renderParamsSlot({
                key: 'requiredMark',
                slots,
              })
            : requiredMark === 'optional'
              ? requiredMark
              : requiredMarkFunction || requiredMark
        }
        feedbackIcons={feedbackIconsFunction}
        onValuesChange={(changedValues, values: any) => {
          onValueChange(values);
          onValuesChange?.(changedValues, values);
        }}
      >
        {children}
      </AForm>
    );
  }
);

export default Form;

"use client";

type RepeatableGroupItem = Record<string, string>;

interface RepeatableGroupFieldProps {
  itemLabel: string;
  fieldNames: string[];
  value: RepeatableGroupItem[];
  onChange: (value: RepeatableGroupItem[]) => void;
  fieldLabelResolver?: (fieldName: string) => string;
  itemDescription?: string;
  addButtonLabel?: string;
}

function humanizeFieldName(fieldName: string): string {
  return fieldName
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function RepeatableGroupField({
  itemLabel,
  fieldNames,
  value,
  onChange,
  fieldLabelResolver,
  itemDescription,
  addButtonLabel,
}: RepeatableGroupFieldProps): JSX.Element {
  const items = value.length ? value : [{}];

  function handleItemChange(index: number, fieldName: string, fieldValue: string): void {
    const nextItems = items.map((item, itemIndex) =>
      itemIndex === index ? { ...item, [fieldName]: fieldValue } : item,
    );
    onChange(nextItems);
  }

  function handleAdd(): void {
    onChange([...items, {}]);
  }

  function handleRemove(index: number): void {
    const nextItems = items.filter((_, itemIndex) => itemIndex !== index);
    onChange(nextItems.length ? nextItems : [{}]);
  }

  return (
    <div className="page-stack">
      {items.map((item, index) => (
        <div key={`${itemLabel}-${index}`} className="entity-card">
          <div className="entity-card__header entity-card__header--spread">
            <div>
              <strong>
                {itemLabel} {index + 1}
              </strong>
              <p>{itemDescription ?? "Capture la informacion correspondiente."}</p>
            </div>
            <button type="button" className="ui-button ui-button--ghost" onClick={() => handleRemove(index)}>
              Eliminar
            </button>
          </div>

          <div className="entity-form__grid">
            {fieldNames.map((fieldName) => (
              <label key={`${itemLabel}-${index}-${fieldName}`} className="ui-field">
                <span>{fieldLabelResolver ? fieldLabelResolver(fieldName) : humanizeFieldName(fieldName)}</span>
                <input
                  value={item[fieldName] ?? ""}
                  onChange={(event) => handleItemChange(index, fieldName, event.target.value)}
                />
              </label>
            ))}
          </div>
        </div>
      ))}

      <div className="entity-form__actions">
        <button type="button" className="ui-button ui-button--ghost" onClick={handleAdd}>
          {addButtonLabel ?? `Agregar ${itemLabel.toLowerCase()}`}
        </button>
      </div>
    </div>
  );
}

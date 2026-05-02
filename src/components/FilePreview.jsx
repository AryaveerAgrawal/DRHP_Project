import FileCard from "./FileCard";

function FilePreview({ files, setFiles }) {
  const removeFile = (index) => {
    const updated = [...files];
    updated.splice(index, 1);
    setFiles(updated);
  };

  return (
    <div className="preview-container">
      {files.map((item, index) => (
        <FileCard
          key={index}
          item={item}
          onRemove={() => removeFile(index)}
        />
      ))}
    </div>
  );
}

export default FilePreview;
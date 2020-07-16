import React, { useState, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import PreLoader from '../../components/PreLoader';

const baseStyle = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '20px',
  borderWidth: 2,
  borderRadius: 2,
  borderColor: '#eeeeee',
  borderStyle: 'dashed',
  backgroundColor: '#fafafa',
  color: '#bdbdbd',
  outline: 'none',
  transition: 'border .24s ease-in-out',
};

const activeStyle = {
  borderColor: '#2196f3',
};

const acceptStyle = {
  borderColor: '#00e676',
};

const rejectStyle = {
  borderColor: '#ff1744',
};

function Dropzone(props) {
  const [files, setFiles] = useState([]);
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
    acceptedFiles,
  } = useDropzone({
    accept: [
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ],
    multiple: false,
    onDrop: fs => {
      setFiles(fs);
    },
  });

  const accFiles = files.map(file => <span key={file.path}>{file.path}</span>);

  const style = useMemo(
    () => ({
      ...baseStyle,
      ...(isDragActive ? activeStyle : {}),
      ...(isDragAccept ? acceptStyle : {}),
      ...(isDragReject ? rejectStyle : {}),
    }),
    [isDragActive, isDragReject, isDragAccept],
  );

  const handleChange = event => {
    setNote(event.target.value);
  };

  const handleSubmit = () => {
    setLoading(true);
    props.uploadFile(props.table, note, files).then(() => {
      setLoading(false);
      setNote('');
      setFiles([]);
    });
  };

  return (
    <div className="mb-50">
      <h3 className="mt-50">Step 3: Upload Your Table File</h3>
      <div {...getRootProps({ style })}>
        <input {...getInputProps()} />
        <p className="dz-font">
          Drag 'n' drop your single excel file, or click to select
        </p>
      </div>
      {accFiles.length > 0 && (
        <aside>
          <h4>
            File Name: {accFiles} {'  '}
            <i style={{ color: '#4caf50' }} className="fa fa-check" />
          </h4>
        </aside>
      )}

      <h3 className="mt-50">Step 4: Write Your Note About This Upload</h3>
      <TextField
        disabled={loading}
        required
        fullWidth
        id="upload-note"
        label="Required"
        value={note}
        placeholder="Write your note about this upload file"
        onChange={handleChange}
      />

      <h3 className="mt-50">Step 5: Submit</h3>
      <div className="submit">
        <Button
          fullWidth
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={files.length === 0 || note.length === 0 || loading}
        >
          {loading ? <PreLoader /> : 'Submit'}
        </Button>
      </div>
    </div>
  );
}

export default Dropzone;
